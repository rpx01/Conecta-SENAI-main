"""Rotas para gerenciamento de turmas."""

from flask import Blueprint, request, jsonify, current_app
from conecta_senai.models import db, EmailSecretaria
from sqlalchemy.exc import SQLAlchemyError
from conecta_senai.utils.error_handler import handle_internal_error
from conecta_senai.models.laboratorio_turma import Turma
from conecta_senai.routes.user import verificar_autenticacao, verificar_admin
from conecta_senai.models.treinamento import TurmaTreinamento, InscricaoTreinamento
from conecta_senai.services.email_service import (
    enviar_convocacao,
    notificar_atualizacao_turma,
    EmailService,
)
from conecta_senai.auth import admin_required
from datetime import datetime
import time

turma_bp = Blueprint("turma", __name__)


@turma_bp.route("/turmas", methods=["GET"])
def listar_turmas():
    """
    Lista todas as turmas disponíveis.
    Acessível para todos os usuários autenticados.
    """
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    turmas = Turma.query.all()
    return jsonify([turma.to_dict() for turma in turmas])


@turma_bp.route("/turmas/<int:id>", methods=["GET"])
def obter_turma(id):
    """
    Obtém detalhes de uma turma específica.
    Acessível para todos os usuários autenticados.
    """
    autenticado, _ = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    turma = db.session.get(Turma, id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404

    return jsonify(turma.to_dict())


@turma_bp.route("/turmas", methods=["POST"])
def criar_turma():
    """
    Cria uma nova turma.
    Apenas administradores podem criar turmas.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    # Verifica permissões de administrador
    if not verificar_admin(user):
        return jsonify({"erro": "Permissão negada"}), 403

    data = request.json or {}

    nome = (data.get("nome") or "").strip()

    # Validação de dados
    if not nome:
        return jsonify({"erro": "Nome da turma é obrigatório"}), 400

    # Verifica se já existe uma turma com o mesmo nome
    if Turma.query.filter_by(nome=nome).first():
        return jsonify({"erro": "Já existe uma turma com este nome"}), 400

    # Cria a turma
    try:
        nova_turma = Turma(nome=nome)
        db.session.add(nova_turma)
        db.session.commit()
        return jsonify(nova_turma.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@turma_bp.route("/turmas/<int:id>", methods=["PUT"])
def atualizar_turma(id):
    """
    Atualiza uma turma existente.
    Apenas administradores podem atualizar turmas.
    """
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401
    # Verifica permissões de administrador
    if not verificar_admin(user):
        return jsonify({"erro": "Permissão negada"}), 403

    turma = db.session.get(Turma, id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404

    data = request.json or {}

    nome = (data.get("nome") or "").strip()

    # Validação de dados
    if not nome:
        return jsonify({"erro": "Nome da turma é obrigatório"}), 400

    # Verifica se já existe outra turma com o mesmo nome
    turma_existente = Turma.query.filter_by(nome=nome).first()
    if turma_existente and turma_existente.id != id:
        return jsonify({"erro": "Já existe outra turma com este nome"}), 400

    # Atualiza a turma
    try:
        instrutor_antigo = getattr(turma, "instrutor", None)
        diff = {}
        if turma.nome != nome:
            diff["nome"] = (turma.nome, nome)

        turma.nome = nome
        db.session.commit()

        try:
            notificar_atualizacao_turma(turma, diff, instrutor_antigo)
        except Exception as exc:  # pragma: no cover - log apenas
            current_app.logger.error(
                "Erro ao notificar atualização de turma %s: %s", id, exc
            )

        return jsonify(turma.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@turma_bp.route("/turma/<int:turma_id>", methods=["DELETE"])
def remover_turma(turma_id):
    """Remove uma turma de treinamento e notifica os responsáveis."""
    autenticado, user = verificar_autenticacao(request)
    if not autenticado:
        return jsonify({"erro": "Não autenticado"}), 401

    if not verificar_admin(user):
        return jsonify({"erro": "Permissão negada"}), 403

    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404

    email_service = EmailService()

    # --- Bloco de código adicionado ---
    # Coleta os e-mails da secretaria
    emails_secretaria = [
        result.email for result in db.session.query(EmailSecretaria.email).all()
    ]

    # Prepara os dados para o template do e-mail
    template_data = {
        "turma": turma.nome if hasattr(turma, "nome") else f"Turma {turma.id}",
        "treinamento": turma.treinamento.nome,
        "instrutor": turma.instrutor.nome if turma.instrutor else "Não definido",
        "data_inicio": turma.data_inicio.strftime('%d/%m/%Y'),
        "data_fim": turma.data_fim.strftime('%d/%m/%Y'),
    }

    # Envia e-mail para a secretaria, se houver e-mails cadastrados
    try:
        if emails_secretaria:
            email_service.send_email(
                to=emails_secretaria,
                subject=f"Turma Removida: {turma.nome if hasattr(turma, 'nome') else turma.id}",
                template="email/turma_removida_secretaria.html.j2",
                **template_data,
            )

        # Envia e-mail para o instrutor, se ele existir
        if turma.instrutor and turma.instrutor.email:
            email_service.send_email(
                to=turma.instrutor.email,
                subject=f"Aviso de Remoção de Turma: {turma.nome if hasattr(turma, 'nome') else turma.id}",
                template="email/turma_removida_secretaria.html.j2",  # Reutilizando o mesmo template
                **template_data,
            )
    except Exception as exc:  # pragma: no cover - log apenas
        current_app.logger.error(
            "Erro ao enviar notificação de remoção da turma %s: %s",
            turma_id,
            exc,
        )
    # --- Fim do bloco ---

    try:
        InscricaoTreinamento.query.filter_by(turma_id=turma_id).delete()
        db.session.delete(turma)
        db.session.commit()
        return jsonify({"mensagem": "Turma removida com sucesso"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@turma_bp.post("/treinamentos/turmas/<int:turma_id>/convocar-todos")
@admin_required
def convocar_todos_da_turma(turma_id: int):
    """Convoca todos os participantes de uma turma,
    independente do status anterior."""
    current_app.logger.info(
        "Iniciando convocação para todos os participantes da turma %s.",
        turma_id,
    )

    turma = db.session.get(TurmaTreinamento, turma_id)
    if not turma:
        return jsonify({"erro": "Turma não encontrada"}), 404

    inscricoes_para_convocar = InscricaoTreinamento.query.filter_by(
        turma_id=turma_id
    ).all()

    total_inscricoes = len(inscricoes_para_convocar)
    if total_inscricoes == 0:
        current_app.logger.warning(
            "Nenhuma inscrição encontrada para convocação na turma %s.",
            turma_id,
        )
        return jsonify({"message": "Nenhum participante para convocar."}), 404

    current_app.logger.info(
        "Encontradas %s inscrições para convocar.",
        total_inscricoes,
    )

    convocados_sucesso = 0
    for inscricao in inscricoes_para_convocar:
        try:
            # Pausa para respeitar o limite do provedor de e-mail (2 req/s)
            time.sleep(0.6)
            enviar_convocacao(inscricao, turma)
            inscricao.convocado_em = datetime.utcnow()
            convocados_sucesso += 1
        except Exception as e:  # pragma: no cover - log de erro
            current_app.logger.error(
                "Falha ao convocar participante %s (email: %s): %s",
                inscricao.id,
                inscricao.email,
                e,
            )

    try:
        db.session.commit()
        current_app.logger.info(
            "Commit realizado. %s convocações atualizadas no banco de dados.",
            convocados_sucesso,
        )
    except Exception as e:  # pragma: no cover - log de erro
        db.session.rollback()
        current_app.logger.error(
            "Erro ao commitar as alterações no banco de dados: %s",
            e,
        )
        return (
            jsonify(
                {
                    "error": (
                        "Ocorreu um erro ao salvar o estado das convocações."
                    )
                }
            ),
            500,
        )

    return jsonify(
        {
            "message": (
                f"{convocados_sucesso} de {total_inscricoes} participantes "
                "convocados com sucesso."
            )
        }
    )
