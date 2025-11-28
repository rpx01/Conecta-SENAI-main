"""Rotas para gerenciamento de usuarios."""

from flask import Blueprint, request, jsonify, current_app, g, redirect
import os
import hmac

from conecta_senai.extensions import limiter
from datetime import datetime, timedelta
import jwt
import uuid
from conecta_senai.models import db
from conecta_senai.models.user import User
from conecta_senai.repositories.user_repository import UserRepository
from conecta_senai.models.refresh_token import RefreshToken
import hashlib
from conecta_senai.config.redis import redis_conn
from sqlalchemy.exc import SQLAlchemyError
import requests
from werkzeug.security import check_password_hash
from conecta_senai.utils.error_handler import handle_internal_error
from conecta_senai.auth import (
    verificar_autenticacao,  # noqa: F401 - reexportado para outros módulos
    verificar_admin,
    login_required,
    admin_required,
)
from flask_wtf.csrf import generate_csrf
from conecta_senai.services import user_service
from pydantic import ValidationError
from conecta_senai.schemas.user import UserCreateSchema, UserUpdateSchema

# Reexporta a expressão regular para compatibilidade
PASSWORD_REGEX = user_service.PASSWORD_REGEX

user_bp = Blueprint("user", __name__)

@user_bp.before_request
def verificar_csrf():
    if request.method in {"POST", "PUT", "DELETE"} and request.endpoint != "user.get_csrf_token":
        token_cookie = request.cookies.get("csrf_token")
        token_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRFToken")
        if not token_cookie or not token_header or not hmac.compare_digest(
            token_cookie, token_header
        ):
            return jsonify({"erro": "CSRF token inválido"}), 403


@user_bp.route("/csrf-token", methods=["GET"])
def get_csrf_token():
    token = generate_csrf()
    secure_cookie = current_app.config.get("COOKIE_SECURE", False)
    samesite = current_app.config.get("COOKIE_SAMESITE", "Lax")
    resp = jsonify({"csrf_token": token})
    resp.set_cookie("csrf_token", token, secure=secure_cookie, samesite=samesite)
    return resp


@user_bp.route("/recaptcha/site-key", methods=["GET"])
def obter_site_key():
    """Retorna a site key pública do reCAPTCHA."""
    site_key = current_app.config.get("RECAPTCHA_SITE_KEY")
    return jsonify({"site_key": site_key or ""})


# Funções auxiliares para geração de tokens


def gerar_token_acesso(usuario):
    """Gera um token JWT de acesso para o usuário."""
    payload = {
        "user_id": usuario.id,
        "nome": usuario.nome,
        "perfil": usuario.tipo,
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def _hash_token(token: str) -> str:
    """Return SHA-256 hexadecimal hash for a token."""
    return hashlib.sha256(token.encode()).hexdigest()


def gerar_refresh_token(usuario):
    """Gera e persiste um refresh token para o usuário."""
    exp = datetime.utcnow() + timedelta(days=7)
    payload = {
        "user_id": usuario.id,
        "exp": exp,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    # Confirma que o usuário ainda existe antes de salvar o token
    if not UserRepository.get_by_id(usuario.id):
        current_app.logger.error("Usuário inválido ao gerar refresh token")
        raise ValueError("Usuário inválido")

    rt = RefreshToken(
        user_id=usuario.id,
        token_hash=_hash_token(token),
        expires_at=exp,
        created_at=datetime.utcnow(),
    )
    try:
        db.session.add(rt)
        db.session.commit()
    except Exception as e:  # pragma: no cover - proteção contra falhas de banco
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar refresh token: {str(e)}")
        raise

    return token


def verificar_refresh_token(token):
    """Valida um refresh token e retorna o usuário associado ou None."""
    try:
        dados = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        if dados.get("type") != "refresh":
            return None
        rt = RefreshToken.query.filter_by(
            token_hash=_hash_token(token), revoked=False
        ).first()
        if not rt or rt.is_expired():
            return None
        usuario = UserRepository.get_by_id(dados.get("user_id"))
        return usuario
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@user_bp.route("/usuarios", methods=["GET"])
@admin_required
def listar_usuarios():
    """Lista todos os usuários com paginação.

    ---
    tags:
      - Usuários
    parameters:
      - in: query
        name: page
        schema:
          type: integer
        description: Página atual
      - in: query
        name: per_page
        schema:
          type: integer
        description: Itens por página
    responses:
      200:
        description: Lista paginada de usuários
        content:
          application/json:
            schema:
              type: object
              properties:
                items:
                  type: array
                  items:
                    $ref: '#/components/schemas/User'
                page:
                  type: integer
                per_page:
                  type: integer
                total:
                  type: integer
                pages:
                  type: integer
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    per_page = min(per_page, 100)
    def _normalizar_valor(valor: str | None, *, to_lower: bool = False) -> str | None:
        if not valor:
            return None

        valor_limpo = valor.strip()
        if not valor_limpo:
            return None

        return valor_limpo.lower() if to_lower else valor_limpo

    filtros = {
        "nome": _normalizar_valor(request.args.get("nome", type=str)),
        "email": _normalizar_valor(request.args.get("email", type=str)),
        "tipo": _normalizar_valor(
            request.args.get("tipo", type=str), to_lower=True
        ),
    }

    if filtros["tipo"] not in {None, "admin", "comum", "secretaria"}:
        filtros["tipo"] = None

    paginacao = UserRepository.paginate(
        page,
        per_page,
        nome=filtros["nome"],
        email=filtros["email"],
        tipo=filtros["tipo"],
    )
    return jsonify(
        {
            "items": [u.to_dict() for u in paginacao.items],
            "page": paginacao.page,
            "per_page": paginacao.per_page,
            "total": paginacao.total,
            "pages": paginacao.pages,
        }
    )


@user_bp.route("/usuarios/<int:id>", methods=["GET"])
@login_required
def obter_usuario(id):
    """Obtém detalhes de um usuário específico.

    ---
    tags:
      - Usuários
    parameters:
      - in: path
        name: id
        schema:
          type: integer
        required: true
        description: ID do usuário
    responses:
      200:
        description: Usuário encontrado
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      403:
        description: Permissão negada
      404:
        description: Usuário não encontrado
    """
    user = g.current_user
    if not verificar_admin(user) and user.id != id:
        return jsonify({"erro": "Permissão negada"}), 403

    usuario = UserRepository.get_by_id(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    return jsonify(usuario.to_dict())


@user_bp.route("/usuarios", methods=["POST"])
@limiter.limit("5 per minute")
def criar_usuario():
    """Cria um novo usuário.
    Usuários não autenticados podem criar apenas usuários comuns.
    Administradores podem criar qualquer tipo de usuário.

    ---
    tags:
      - Usuários
    requestBody:
      required: true
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserCreate'
    responses:
      201:
        description: Usuário criado
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      400:
        description: Erro de validação
    """
    try:
        payload = UserCreateSchema(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify({"erro": e.errors()[0]["msg"]}), 400

    try:
        novo_usuario, erro = user_service.criar_usuario(payload.model_dump(by_alias=True))
    except SQLAlchemyError as e:
        return handle_internal_error(e)

    if erro:
        return jsonify(erro[0]), erro[1]

    return jsonify(novo_usuario.to_dict()), 201


@user_bp.route("/registrar", methods=["POST"])
def registrar_usuario():
    """Registra um usuário a partir de um formulário HTML ou JSON."""
    origem = request.get_json() if request.is_json else request.form
    dados = {
        "nome": (origem.get("nome") or "").strip(),
        "email": (origem.get("email") or "").strip(),
        "senha": origem.get("senha"),
        "confirmarSenha": origem.get("confirmarSenha"),
        "username": origem.get("username"),
    }

    try:
        payload = UserCreateSchema(**dados)
    except ValidationError as e:
        return jsonify({"erro": e.errors()[0]["msg"]}), 400

    try:
        _, erro = user_service.criar_usuario(payload.model_dump(by_alias=True))
    except SQLAlchemyError as e:  # pragma: no cover
        return handle_internal_error(e)

    if erro:
        return jsonify(erro[0]), erro[1]

    if request.is_json:
        return jsonify({"mensagem": "Usuário registrado com sucesso"}), 201
    return redirect("/admin/login.html")


@user_bp.route("/usuarios/<int:id>", methods=["PUT"])
@login_required
def atualizar_usuario(id):
    """
    Atualiza um usuário existente.
    Usuários comuns só podem atualizar seus próprios dados.
    Administradores podem atualizar dados de qualquer usuário.
    """
    user = g.current_user

    # Verifica permissões
    if not verificar_admin(user) and user.id != id:
        return jsonify({"erro": "Permissão negada"}), 403

    usuario = UserRepository.get_by_id(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    try:
        dados = UserUpdateSchema(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify({"erro": e.errors()[0]["msg"]}), 400

    data = dados.model_dump(exclude_unset=True)

    # Atualiza os campos fornecidos
    if "nome" in data:
        usuario.nome = data["nome"]

    if "email" in data:
        email_existente = UserRepository.get_by_email(data["email"])
        if email_existente and email_existente.id != id:
            return jsonify({"erro": "Email já cadastrado"}), 400
        usuario.email = data["email"]

    if "cpf" in data:
        usuario.cpf = data["cpf"]
    if "empresa" in data:
        usuario.empresa = data["empresa"]
    if "data_nascimento" in data:
        usuario.data_nascimento = data["data_nascimento"]

    if "tipo" in data and verificar_admin(user):
        novo_tipo = data["tipo"]
        admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
        solicitante_email = (user.email or "").lower()
        alvo_email = (usuario.email or "").lower()
        is_root_solicitante = bool(admin_email) and solicitante_email == admin_email
        is_root_alvo = bool(admin_email) and alvo_email == admin_email

        if is_root_alvo and not is_root_solicitante:
            return (
                jsonify(
                    {"erro": "Você não tem permissão para alterar o Administrador raiz"}
                ),
                403,
            )

        if (
            usuario.tipo == "admin"
            and novo_tipo != "admin"
            and not is_root_solicitante
        ):
            return (
                jsonify(
                    {
                        "erro": "Você não tem permissão para alterar o tipo de administrador para comum"
                    }
                ),
                403,
            )

        usuario.tipo = novo_tipo

    if "senha" in data:
        senha_atual = data.get("senha_atual")

        if not verificar_admin(user) or user.id == id:
            if not senha_atual:
                return jsonify({"erro": "Senha atual obrigatória"}), 400
            if not usuario.check_senha(senha_atual):
                return jsonify({"erro": "Senha atual incorreta"}), 403

        usuario.set_senha(data["senha"])

    try:
        UserRepository.commit()
        return jsonify(usuario.to_dict())
    except SQLAlchemyError as e:
        UserRepository.rollback()
        return handle_internal_error(e)


@user_bp.route("/usuarios/<int:id>", methods=["DELETE"])
@admin_required
def remover_usuario(id):
    """
    Remove um usuário.
    Apenas administradores podem remover usuários.
    Um usuário não pode remover a si mesmo.
    """
    user = g.current_user

    # Impede que um usuário remova a si mesmo
    if user.id == id:
        return jsonify({"erro": "Não é possível remover o próprio usuário"}), 400

    usuario = UserRepository.get_by_id(id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    solicitante_email = (user.email or "").lower()
    alvo_email = (usuario.email or "").lower()
    is_root_solicitante = bool(admin_email) and solicitante_email == admin_email
    is_root_alvo = bool(admin_email) and alvo_email == admin_email

    # Protege o administrador raiz contra remoção por outros usuários
    if is_root_alvo and not is_root_solicitante:
        return (
            jsonify({"erro": "Você não tem permissão para remover o Administrador raiz"}),
            403,
        )

    # Apenas o administrador raiz pode remover outros administradores
    if usuario.tipo == "admin" and not is_root_solicitante:
        return (
            jsonify({"erro": "Você não tem permissão para remover um administrador"}),
            403,
        )

    try:
        UserRepository.delete(usuario)
        return jsonify({"mensagem": "Usuário removido com sucesso"})
    except SQLAlchemyError as e:
        UserRepository.rollback()
        return handle_internal_error(e)


@user_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """Autentica um usuário e retorna tokens JWT.

    ---
    tags:
      - Autenticação
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
              senha:
                type: string
              recaptcha_token:
                type: string
            required:
              - email
              - senha
    responses:
      200:
        description: Tokens de acesso e refresh
        content:
          application/json:
            schema:
              type: object
              properties:
                access_token:
                  type: string
                refresh_token:
                  type: string
      400:
        description: Requisição inválida
    """
    try:
        dados = request.get_json(silent=True)

        if not dados:
            return jsonify(success=False, message="Corpo da requisição ausente"), 400

        email = dados.get("email", "").strip()
        senha = dados.get("senha")
        recaptcha_token = dados.get("recaptcha_token")

        # Valida reCAPTCHA caso a chave esteja configurada
        recaptcha_secret = (current_app.config.get("RECAPTCHA_SECRET_KEY") or "").strip()
        recaptcha_site_key = (current_app.config.get("RECAPTCHA_SITE_KEY") or "").strip()
        if recaptcha_secret and recaptcha_site_key:
            if not recaptcha_token:
                return (
                    jsonify(success=False, message="Verificação reCAPTCHA obrigatória"),
                    400,
                )
            try:
                verify_resp = requests.post(
                    "https://www.google.com/recaptcha/api/siteverify",
                    data={"secret": recaptcha_secret, "response": recaptcha_token},
                    timeout=5,
                )
                verify_data = verify_resp.json()
                threshold = current_app.config.get("RECAPTCHA_THRESHOLD", 0.5)
                if (
                    not verify_data.get("success")
                    or verify_data.get("action") != "login"
                    or verify_data.get("score", 0) < threshold
                ):
                    return (
                        jsonify(
                            success=False,
                            message="Verificação reCAPTCHA falhou. Tente novamente.",
                        ),
                        400,
                    )
            except requests.RequestException:
                return (
                    jsonify(success=False, message="Falha ao verificar reCAPTCHA"),
                    400,
                )

        if not email or not senha:
            return jsonify(success=False, message="Email e senha são obrigatórios"), 400

        usuario = UserRepository.get_by_email(email)

        try:
            senha_ok = usuario and check_password_hash(usuario.senha_hash, senha)
        except ValueError:
            senha_ok = False

        if not senha_ok:
            current_app.logger.warning(
                "Tentativa de login inválida para %s do IP %s",
                email,
                request.remote_addr,
            )
            return jsonify(success=False, message="Credenciais inválidas"), 401

        access_token = gerar_token_acesso(usuario)
        try:
            refresh_token = gerar_refresh_token(usuario)
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar refresh token: {e}")
            return jsonify(success=False, message="Erro ao salvar token"), 500

        secure_cookie = current_app.config.get("COOKIE_SECURE", True)
        csrf_token = generate_csrf()
        admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
        usuario_dict = usuario.to_dict()
        is_root = bool(admin_email) and (usuario.email or "").strip().lower() == admin_email
        usuario_dict["is_root"] = is_root
        resp = jsonify(
            message="Login successful",
            token=access_token,
            refresh_token=refresh_token,
            usuario=usuario_dict,
            csrf_token=csrf_token,
            is_root=is_root,
        )
        resp.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            secure=secure_cookie,
            samesite="Strict",
        )
        resp.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="Strict",
        )
        resp.set_cookie(
            "csrf_token",
            csrf_token,
            secure=secure_cookie,
            samesite="Strict",
        )
        return resp, 200
    except SQLAlchemyError as e:
        UserRepository.rollback()
        current_app.logger.error(f"Erro ao fazer login: {e}")
        return jsonify(success=False, message="Erro interno no login"), 500
    except Exception as e:
        current_app.logger.error(f"Erro inesperado ao fazer login: {e}")
        return jsonify(success=False, message="Erro interno no login"), 500


@user_bp.route("/refresh", methods=["POST"])
def refresh_token():
    data = request.json or {}
    token = data.get("refresh_token") or request.cookies.get("refresh_token")
    if not token:
        return jsonify({"erro": "Refresh token obrigatório"}), 400
    usuario = verificar_refresh_token(token)
    if not usuario:
        return jsonify({"erro": "Refresh token inválido"}), 401
    novo_token = gerar_token_acesso(usuario)
    secure_cookie = current_app.config.get("COOKIE_SECURE", True)
    csrf_token = generate_csrf()
    resp = jsonify({"token": novo_token, "csrf_token": csrf_token})
    resp.set_cookie(
        "access_token",
        novo_token,
        httponly=True,
        secure=secure_cookie,
        samesite="Strict",
    )
    resp.set_cookie(
        "csrf_token",
        csrf_token,
        secure=secure_cookie,
        samesite="Strict",
    )
    return resp


@user_bp.route("/logout", methods=["POST"])
def logout():
    """Revoga o token de acesso atual e/ou o refresh token."""
    auth_header = request.headers.get("Authorization")
    token = (
        auth_header.split(" ")[1]
        if auth_header
        else request.cookies.get("access_token")
    )

    if token:
        try:
            dados = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            jti = dados.get("jti")
            exp = datetime.utcfromtimestamp(dados["exp"])
            ttl = exp - datetime.utcnow()
            if ttl.total_seconds() > 0 and jti:
                redis_conn.setex(jti, ttl, "revoked")
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido"}), 401

    data = request.json or {}
    refresh = data.get("refresh_token") or request.cookies.get("refresh_token")
    if refresh:
        rt = RefreshToken.query.filter_by(token_hash=_hash_token(refresh)).first()
        if rt:
            rt.revoked = True
            db.session.commit()

    if not token and not refresh:
        return jsonify({"erro": "Token obrigatório"}), 400

    secure_cookie = current_app.config.get("COOKIE_SECURE", True)
    resp = jsonify({"mensagem": "Logout realizado"})
    resp.set_cookie(
        "access_token",
        "",
        expires=0,
        secure=secure_cookie,
        samesite="Strict",
    )
    resp.set_cookie(
        "refresh_token",
        "",
        expires=0,
        secure=secure_cookie,
        samesite="Strict",
    )
    resp.set_cookie(
        "csrf_token",
        "",
        expires=0,
        secure=secure_cookie,
        samesite="Strict",
    )
    return resp
