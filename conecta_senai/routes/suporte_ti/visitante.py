"""Rotas públicas para abertura de chamados por visitantes."""
from __future__ import annotations

from flask import Blueprint, jsonify, render_template, request
from flask_wtf.csrf import CSRFError, validate_csrf
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from wtforms.validators import ValidationError

from conecta_senai.models import db
from conecta_senai.models.suporte_basedados import SuporteArea, SuporteTipoEquipamento
from conecta_senai.models.suporte_chamado import SuporteChamado
from conecta_senai.routes.suporte_ti.utils import ensure_tables_exist

suporte_ti_visitante_bp = Blueprint(
    "suporte_ti_visitante",
    __name__,
    url_prefix="/suporte",
)

suporte_ti_paginas_publicas_bp = Blueprint(
    "suporte_ti_paginas_publicas",
    __name__,
)

ALLOWED_URGENCIAS = {"Baixo", "Médio", "Medio", "Alto"}
CHAMADO_EMAIL_MAX_LEN = (
    SuporteChamado.email.property.columns[0].type.length or 120
)
CHAMADO_AREA_MAX_LEN = SuporteChamado.area.property.columns[0].type.length or 120


def _limpar_texto(valor: str | None, limite: int | None = None) -> str:
    if not valor:
        return ""
    texto = valor.strip()
    if limite is not None:
        return texto[:limite]
    return texto


def _recuperar_payload() -> dict:
    if request.is_json:
        return request.get_json(silent=True) or {}
    return {}


def _obter_dado(form, payload, *chaves):
    for chave in chaves:
        if chave in form:
            return form.get(chave)
        if chave in payload:
            return payload.get(chave)
    return None


def _normalizar_urgencia(valor: str | None) -> str:
    if not valor:
        return "Médio"
    texto = valor.strip()
    if texto in {"Medio", "medio"}:
        return "Médio"
    return texto


@suporte_ti_paginas_publicas_bp.route(
    "/suporte_ti/abertura_publica.html", methods=["GET"], strict_slashes=False
)
def pagina_abertura_publica():
    """Renderiza o formulário público de abertura de chamados com dados padrão."""

    form_data = request.args.to_dict(flat=True) if request.args else {}
    return render_template(
        "suporte_ti/abertura_publica.html",
        form_data=form_data or {},
    )


@suporte_ti_visitante_bp.route("/base-dados", methods=["GET"])
def obter_base_dados_visitante():
    """Retorna as áreas e tipos de equipamento disponíveis para o formulário público."""

    ensure_tables_exist([SuporteTipoEquipamento, SuporteArea])

    tipos = SuporteTipoEquipamento.query.order_by(SuporteTipoEquipamento.nome.asc()).all()
    areas = SuporteArea.query.order_by(SuporteArea.nome.asc()).all()

    return jsonify(
        {
            "tipos_equipamento": [
                {"id": tipo.id, "nome": tipo.nome} for tipo in tipos
            ],
            "areas": [{"id": area.id, "nome": area.nome} for area in areas],
        }
    )


@suporte_ti_visitante_bp.route("/abrir-chamado", methods=["POST"])
def abrir_chamado_publico():
    """Cria um novo chamado de suporte enviado por um visitante não autenticado."""

    ensure_tables_exist([SuporteArea, SuporteTipoEquipamento, SuporteChamado])

    form = request.form
    payload = _recuperar_payload()

    csrf_token = _obter_dado(form, payload, "csrf_token")
    if not csrf_token:
        return jsonify({"erro": "Token CSRF ausente."}), 400
    try:
        validate_csrf(csrf_token)
    except (CSRFError, ValidationError):
        return jsonify({"erro": "Token CSRF inválido."}), 400

    nome = _limpar_texto(_obter_dado(form, payload, "nome_completo", "nome"), 150)
    email = _limpar_texto(
        _obter_dado(form, payload, "email", "email_contato"), CHAMADO_EMAIL_MAX_LEN
    )
    area = _limpar_texto(
        _obter_dado(form, payload, "area"), CHAMADO_AREA_MAX_LEN
    )
    tipo_equipamento_id = _obter_dado(
        form, payload, "tipo_equipamento_id", "tipoEquipamentoId"
    )
    patrimonio = _limpar_texto(_obter_dado(form, payload, "patrimonio"), 120)
    numero_serie = _limpar_texto(_obter_dado(form, payload, "numero_serie", "numeroSerie"), 120)
    descricao = _limpar_texto(
        _obter_dado(
            form,
            payload,
            "descricao_problema",
            "descricaoProblema",
            "descricao",
        )
    )
    nivel_urgencia = _limpar_texto(
        _obter_dado(form, payload, "nivel_urgencia", "nivelUrgencia"),
        20,
    )
    local_unidade = _limpar_texto(
        _obter_dado(form, payload, "local_unidade", "local", "unidade"),
        150,
    )

    erros: list[str] = []

    if not nome:
        erros.append("Informe o nome completo.")
    if not email or "@" not in email:
        erros.append("Informe um e-mail válido.")
    if not area:
        erros.append("Selecione a área responsável.")
    if not tipo_equipamento_id:
        erros.append("Selecione o tipo de equipamento.")
    if not descricao:
        erros.append("Descreva o problema encontrado.")

    if not nivel_urgencia:
        nivel_urgencia = "Médio"
    elif nivel_urgencia not in ALLOWED_URGENCIAS:
        erros.append("Nível de urgência inválido.")

    area_registro = None
    if area:
        area_registro = (
            SuporteArea.query.filter(func.lower(SuporteArea.nome) == area.lower())
            .first()
        )
        if not area_registro:
            erros.append("Área selecionada não está cadastrada.")

    try:
        tipo_id = int(tipo_equipamento_id) if tipo_equipamento_id is not None else None
    except (ValueError, TypeError):
        tipo_id = None
        erros.append("Tipo de equipamento inválido.")

    tipo_equipamento = None
    if tipo_id is not None:
        tipo_equipamento = db.session.get(SuporteTipoEquipamento, tipo_id)
        if not tipo_equipamento:
            erros.append("Tipo de equipamento não encontrado.")

    if erros:
        return jsonify({"erro": erros}), 400

    chamado = SuporteChamado(
        user_id=None,
        nome_solicitante=nome,
        email=email,
        area=area_registro.nome if area_registro else area,
        tipo_equipamento_id=tipo_equipamento.id if tipo_equipamento else None,
        patrimonio=patrimonio or None,
        numero_serie=numero_serie or None,
        descricao_problema=descricao,
        nivel_urgencia=_normalizar_urgencia(nivel_urgencia),
        status="Aberto",
        local_unidade=local_unidade or None,
    )

    try:
        db.session.add(chamado)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Não foi possível registrar o chamado."}), 500

    return jsonify({"mensagem": "Chamado registrado com sucesso.", "id": chamado.id}), 201
