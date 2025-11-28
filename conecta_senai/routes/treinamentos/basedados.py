"""Rotas auxiliares relacionadas à secretaria de treinamentos."""

from flask import Blueprint, jsonify, request
from pydantic import ValidationError
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from conecta_senai.auth import admin_required
from conecta_senai.models import db
from conecta_senai.models.secretaria_treinamentos import SecretariaTreinamentos
from conecta_senai.models.treinamento import LocalRealizacao
from conecta_senai.models.horario import Horario
from conecta_senai.schemas.secretaria_treinamentos import SecretariaTreinamentosSchema
from conecta_senai.schemas.treinamento import LocalRealizacaoSchema
from conecta_senai.schemas.horario import HorarioIn, HorarioOut
from conecta_senai.services.horario_service import create_horario, update_horario

secretaria_bp = Blueprint("treinamentos_secretaria", __name__)
locais_realizacao_bp = Blueprint("treinamentos_locais_realizacao", __name__)
horarios_bp = Blueprint("treinamentos_horarios", __name__)

schema = SecretariaTreinamentosSchema()
schemas = SecretariaTreinamentosSchema(many=True)


def _serialize_local(local: LocalRealizacao) -> dict:
    return LocalRealizacaoSchema.model_validate(local).model_dump()


def _validar_local_payload(data: dict):
    try:
        payload = LocalRealizacaoSchema.model_validate(data)
    except ValidationError as exc:
        return None, exc.errors()
    nome = payload.nome.strip()
    if not nome:
        return None, [
            {
                "loc": ("nome",),
                "msg": "Nome não pode ser vazio",
                "type": "value_error",
            }
        ]
    return nome, None


def ensure_table_exists(model) -> None:
    """Cria a tabela do modelo caso não exista."""
    inspector = inspect(db.engine)
    if not inspector.has_table(model.__tablename__):
        model.__table__.create(db.engine)


@secretaria_bp.route("", methods=["GET"])
@admin_required
def listar_contatos():
    ensure_table_exists(SecretariaTreinamentos)
    contatos = (
        SecretariaTreinamentos.query.order_by(SecretariaTreinamentos.id).all()
    )
    return jsonify(schemas.dump(contatos))


@secretaria_bp.route("", methods=["POST"])
@admin_required
def criar_contato():
    ensure_table_exists(SecretariaTreinamentos)
    data = request.get_json() or {}
    erros = schema.validate(data)
    if erros:
        return jsonify({"erro": erros}), 400
    if SecretariaTreinamentos.query.filter_by(email=data.get("email")).first():
        return jsonify({"erro": "E-mail já cadastrado"}), 409
    contato = SecretariaTreinamentos(nome=data["nome"], email=data["email"])
    try:
        db.session.add(contato)
        db.session.commit()
        return schema.dump(contato), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar contato"}), 500


@secretaria_bp.route("/<int:contato_id>", methods=["PUT"])
@admin_required
def atualizar_contato(contato_id):
    ensure_table_exists(SecretariaTreinamentos)
    contato = db.session.get(SecretariaTreinamentos, contato_id)
    if not contato:
        return jsonify({"erro": "Contato não encontrado"}), 404
    data = request.get_json() or {}
    erros = schema.validate(data)
    if erros:
        return jsonify({"erro": erros}), 400
    if (
        SecretariaTreinamentos.query.filter(
            SecretariaTreinamentos.email == data.get("email"),
            SecretariaTreinamentos.id != contato_id,
        ).first()
    ):
        return jsonify({"erro": "E-mail já cadastrado"}), 409
    contato.nome = data["nome"]
    contato.email = data["email"]
    try:
        db.session.commit()
        return schema.dump(contato)
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar contato"}), 500


@secretaria_bp.route("/<int:contato_id>", methods=["DELETE"])
@admin_required
def excluir_contato(contato_id):
    ensure_table_exists(SecretariaTreinamentos)
    contato = db.session.get(SecretariaTreinamentos, contato_id)
    if not contato:
        return jsonify({"erro": "Contato não encontrado"}), 404
    try:
        db.session.delete(contato)
        db.session.commit()
        return jsonify({"mensagem": "Contato excluído com sucesso"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir contato"}), 500


@locais_realizacao_bp.route("", methods=["GET"])
@admin_required
def listar_locais_realizacao():
    ensure_table_exists(LocalRealizacao)
    locais = LocalRealizacao.query.order_by(LocalRealizacao.id).all()
    return jsonify([_serialize_local(local) for local in locais])


@locais_realizacao_bp.route("", methods=["POST"])
@admin_required
def criar_local_realizacao():
    ensure_table_exists(LocalRealizacao)
    data = request.get_json() or {}
    nome, erros = _validar_local_payload(data)
    if erros:
        return jsonify({"erro": erros}), 400
    if LocalRealizacao.query.filter_by(nome=nome).first():
        return jsonify({"erro": "Local já cadastrado"}), 409
    local = LocalRealizacao(nome=nome)
    try:
        db.session.add(local)
        db.session.commit()
        return _serialize_local(local), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar local"}), 500


@locais_realizacao_bp.route("/<int:local_id>", methods=["PUT"])
@admin_required
def atualizar_local_realizacao(local_id):
    ensure_table_exists(LocalRealizacao)
    local = db.session.get(LocalRealizacao, local_id)
    if not local:
        return jsonify({"erro": "Local não encontrado"}), 404
    data = request.get_json() or {}
    nome, erros = _validar_local_payload(data)
    if erros:
        return jsonify({"erro": erros}), 400
    if (
        LocalRealizacao.query.filter(
            LocalRealizacao.nome == nome,
            LocalRealizacao.id != local_id,
        ).first()
    ):
        return jsonify({"erro": "Local já cadastrado"}), 409
    local.nome = nome
    try:
        db.session.commit()
        return _serialize_local(local)
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar local"}), 500


@locais_realizacao_bp.route("/<int:local_id>", methods=["DELETE"])
@admin_required
def excluir_local_realizacao(local_id):
    ensure_table_exists(LocalRealizacao)
    local = db.session.get(LocalRealizacao, local_id)
    if not local:
        return jsonify({"erro": "Local não encontrado"}), 404
    try:
        db.session.delete(local)
        db.session.commit()
        return jsonify({"mensagem": "Local excluído com sucesso"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir local"}), 500


@horarios_bp.route('', methods=['GET'])
@admin_required
def listar_horarios():
    """Lista todos os horários cadastrados ordenados por nome."""

    ensure_table_exists(Horario)
    horarios = Horario.query.order_by(Horario.nome).all()
    return jsonify([HorarioOut.model_validate(h).model_dump() for h in horarios])


@horarios_bp.route('', methods=['POST'])
@admin_required
def criar_horario():
    """Cria um novo horário disponível para treinamentos."""

    ensure_table_exists(Horario)
    payload = request.get_json() or {}
    try:
        data = HorarioIn.model_validate(payload)
    except ValidationError as exc:
        return jsonify({"erro": exc.errors()}), 400

    nome = data.nome.strip()
    if Horario.query.filter_by(nome=nome).first():
        return jsonify({"erro": "Horário já cadastrado"}), 409

    horario = create_horario(data.model_dump())
    return HorarioOut.model_validate(horario).model_dump(), 201


@horarios_bp.route('/<int:horario_id>', methods=['PUT'])
@admin_required
def atualizar_horario(horario_id: int):
    """Atualiza os dados de um horário existente."""

    ensure_table_exists(Horario)
    horario = db.session.get(Horario, horario_id)
    if not horario:
        return jsonify({"erro": "Horário não encontrado"}), 404

    payload = request.get_json() or {}
    try:
        data = HorarioIn.model_validate(payload)
    except ValidationError as exc:
        return jsonify({"erro": exc.errors()}), 400

    nome = data.nome.strip()
    if Horario.query.filter(Horario.nome == nome, Horario.id != horario_id).first():
        return jsonify({"erro": "Horário já cadastrado"}), 409

    horario_atualizado = update_horario(horario, data.model_dump())
    return HorarioOut.model_validate(horario_atualizado).model_dump()
