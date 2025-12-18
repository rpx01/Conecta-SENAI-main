from flask import Blueprint, request, jsonify
from conecta_senai.models import db
from sqlalchemy.exc import SQLAlchemyError
from conecta_senai.utils.error_handler import handle_internal_error
from conecta_senai.models.sala import Sala
from conecta_senai.models.recurso import Recurso
from conecta_senai.models.ocupacao import Ocupacao
from conecta_senai.routes.user import verificar_autenticacao, verificar_admin
from datetime import datetime, date
from pydantic import ValidationError
from conecta_senai.schemas import SalaCreateSchema, SalaUpdateSchema

sala_bp = Blueprint("sala", __name__)


@sala_bp.route("/salas", methods=["GET"])
def listar_salas():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    status = request.args.get("status")
    tipo = request.args.get("tipo")
    capacidade_min = request.args.get("capacidade_min", type=int)

    query = Sala.query

    if status:
        query = query.filter(Sala.status == status)

    if tipo:
        query = query.filter(Sala.tipo == tipo)

    if capacidade_min:
        query = query.filter(Sala.capacidade >= capacidade_min)

    salas = query.order_by(Sala.nome).all()

    return jsonify([sala.to_dict() for sala in salas])


@sala_bp.route("/salas/<int:id>", methods=["GET"])
def obter_sala(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    sala = db.session.get(Sala, id)
    if not sala:
        return jsonify({"erro": "Sala não encontrada"}), 404

    return jsonify(sala.to_dict())


@sala_bp.route("/salas", methods=["POST"])
def criar_sala():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    if not verificar_admin(user):
        return jsonify({"erro": "Permissão negada"}), 403

    data = request.json or {}
    try:
        payload = SalaCreateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    if Sala.query.filter_by(nome=payload.nome).first():
        return jsonify({"erro": "Já existe uma sala com este nome"}), 400

    status_validos = ["ativa", "inativa", "manutencao"]
    status = payload.status or "ativa"
    if status not in status_validos:
        return (
            jsonify(
                {
                    "erro": f'Status deve ser um dos seguintes: {", ".join(status_validos)}'
                }
            ),
            400,
        )

    try:
        nova_sala = Sala(
            nome=payload.nome,
            capacidade=payload.capacidade,
            recursos=payload.recursos,
            localizacao=payload.localizacao,
            tipo=payload.tipo,
            status=status,
            observacoes=payload.observacoes,
        )

        db.session.add(nova_sala)
        db.session.commit()

        return jsonify(nova_sala.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@sala_bp.route("/salas/<int:id>", methods=["PUT"])
def atualizar_sala(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    if not verificar_admin(user):
        return jsonify({"erro": "Permissão negada"}), 403

    sala = db.session.get(Sala, id)
    if not sala:
        return jsonify({"erro": "Sala não encontrada"}), 404

    data = request.json or {}
    try:
        payload = SalaUpdateSchema(**data)
    except ValidationError as e:
        return jsonify({"erro": e.errors()}), 400

    if payload.nome is not None:

        sala_existente = Sala.query.filter_by(nome=payload.nome).first()
        if sala_existente and sala_existente.id != id:
            return jsonify({"erro": "Já existe uma sala com este nome"}), 400
        sala.nome = payload.nome

    if payload.capacidade is not None:
        sala.capacidade = payload.capacidade

    if payload.recursos is not None:
        recursos_nomes = payload.recursos
        sala.recursos.clear()
        for nome_recurso in recursos_nomes:
            recurso = Recurso.query.filter_by(nome=nome_recurso).first()
            if not recurso:
                recurso = Recurso(nome=nome_recurso)
                db.session.add(recurso)
            sala.recursos.append(recurso)

    if payload.localizacao is not None:
        sala.localizacao = payload.localizacao

    if payload.tipo is not None:
        sala.tipo = payload.tipo

    if payload.status is not None:
        status_validos = ["ativa", "inativa", "manutencao"]
        if payload.status not in status_validos:
            return (
                jsonify(
                    {
                        "erro": f'Status deve ser um dos seguintes: {", ".join(status_validos)}'
                    }
                ),
                400,
            )
        sala.status = payload.status

    if payload.observacoes is not None:
        sala.observacoes = payload.observacoes

    try:
        db.session.commit()
        return jsonify(sala.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@sala_bp.route("/salas/<int:id>", methods=["DELETE"])
def remover_sala(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    if not verificar_admin(user):
        return jsonify({"erro": "Permissão negada"}), 403

    sala = db.session.get(Sala, id)
    if not sala:
        return jsonify({"erro": "Sala não encontrada"}), 404

    ocupacoes_futuras = Ocupacao.query.filter(
        Ocupacao.sala_id == id,
        Ocupacao.data >= date.today(),
        Ocupacao.status.in_(["confirmado", "pendente"]),
    ).count()

    if ocupacoes_futuras > 0:
        return (
            jsonify({"erro": "Não é possível remover sala com ocupações futuras"}),
            400,
        )

    try:
        db.session.delete(sala)
        db.session.commit()
        return jsonify({"mensagem": "Sala removida com sucesso"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@sala_bp.route("/salas/<int:id>/disponibilidade", methods=["GET"])
def verificar_disponibilidade_sala(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    sala = db.session.get(Sala, id)
    if not sala:
        return jsonify({"erro": "Sala não encontrada"}), 404

    data_str = request.args.get("data")
    horario_inicio_str = request.args.get("horario_inicio")
    horario_fim_str = request.args.get("horario_fim")
    ocupacao_id = request.args.get("ocupacao_id", type=int)

    if not all([data_str, horario_inicio_str, horario_fim_str]):
        return jsonify({"erro": "Data, horário de início e fim são obrigatórios"}), 400

    try:

        data_verificacao = datetime.strptime(data_str, "%Y-%m-%d").date()
        horario_inicio = datetime.strptime(horario_inicio_str, "%H:%M").time()
        horario_fim = datetime.strptime(horario_fim_str, "%H:%M").time()

        disponivel = sala.is_disponivel(
            data_verificacao, horario_inicio, horario_fim, ocupacao_id
        )

        conflitos = []
        if not disponivel:
            ocupacoes_conflitantes = Ocupacao.buscar_conflitos(
                id, data_verificacao, horario_inicio, horario_fim, ocupacao_id
            )
            conflitos = [
                ocupacao.to_dict(include_relations=False)
                for ocupacao in ocupacoes_conflitantes
            ]

        return jsonify(
            {"disponivel": disponivel, "sala": sala.to_dict(), "conflitos": conflitos}
        )

    except ValueError:
        return jsonify({"erro": "Formato de data ou horário inválido"}), 400
    except SQLAlchemyError as e:
        return handle_internal_error(e)


@sala_bp.route("/salas/<int:id>/ocupacoes", methods=["GET"])
def listar_ocupacoes_sala(id):
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    sala = db.session.get(Sala, id)
    if not sala:
        return jsonify({"erro": "Sala não encontrada"}), 404

    data_inicio_str = request.args.get("data_inicio")
    data_fim_str = request.args.get("data_fim")
    status = request.args.get("status")

    query = Ocupacao.query.filter(Ocupacao.sala_id == id)

    if data_inicio_str:
        try:
            data_inicio = datetime.strptime(data_inicio_str, "%Y-%m-%d").date()
            query = query.filter(Ocupacao.data >= data_inicio)
        except ValueError:
            return (
                jsonify({"erro": "Formato de data_inicio inválido (YYYY-MM-DD)"}),
                400,
            )

    if data_fim_str:
        try:
            data_fim = datetime.strptime(data_fim_str, "%Y-%m-%d").date()
            query = query.filter(Ocupacao.data <= data_fim)
        except ValueError:
            return jsonify({"erro": "Formato de data_fim inválido (YYYY-MM-DD)"}), 400

    if status:
        query = query.filter(Ocupacao.status == status)

    ocupacoes = query.order_by(Ocupacao.data, Ocupacao.horario_inicio).all()

    return jsonify(
        {
            "sala": sala.to_dict(),
            "ocupacoes": [ocupacao.to_dict() for ocupacao in ocupacoes],
        }
    )


@sala_bp.route("/salas/tipos", methods=["GET"])
def listar_tipos_sala():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    tipos = [
        {"valor": "aula_teorica", "nome": "Aula Teórica"},
        {"valor": "laboratorio", "nome": "Laboratório"},
        {"valor": "auditorio", "nome": "Auditório"},
        {"valor": "sala_reuniao", "nome": "Sala de Reunião"},
        {"valor": "sala_multiuso", "nome": "Sala Multiuso"},
        {"valor": "biblioteca", "nome": "Biblioteca"},
        {"valor": "oficina", "nome": "Oficina"},
    ]

    return jsonify(tipos)


@sala_bp.route("/salas/recursos", methods=["GET"])
def listar_recursos_disponiveis():
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    recursos = Recurso.query.order_by(Recurso.nome).all()
    return jsonify(
        [{"valor": r.nome, "nome": r.nome.replace("_", " ").title()} for r in recursos]
    )
