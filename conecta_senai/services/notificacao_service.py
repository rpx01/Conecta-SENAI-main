from flask import jsonify
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError

from conecta_senai.models import db
from conecta_senai.models.agendamento import Notificacao, Agendamento
from conecta_senai.routes.user import verificar_admin
from conecta_senai.utils.error_handler import handle_internal_error


def listar_notificacoes(user):
    """Retorna notificações ordenadas por data de criação."""
    if verificar_admin(user):
        notificacoes = Notificacao.query.order_by(Notificacao.data_criacao.desc()).all()
    else:
        notificacoes = Notificacao.query.filter_by(usuario_id=user.id).order_by(
            Notificacao.data_criacao.desc()
        ).all()
    return jsonify([n.to_dict() for n in notificacoes])


def marcar_notificacao_lida(id, user):
    """Marca uma notificação como lida se o usuário tiver permissão."""
    notificacao = db.session.get(Notificacao, id)
    if not notificacao:
        return jsonify({'erro': 'Notificação não encontrada'}), 404

    if not verificar_admin(user) and notificacao.usuario_id != user.id:
        return jsonify({'erro': 'Permissão negada'}), 403

    try:
        notificacao.marcar_como_lida()
        db.session.commit()
        return jsonify(notificacao.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


def criar_notificacoes_agendamentos_proximos():
    """Gera lembretes para agendamentos que ocorrerão nas próximas 24 horas."""
    agora = datetime.utcnow()
    limite = agora + timedelta(hours=24)

    agendamentos_proximos = Agendamento.query.filter(
        Agendamento.data >= agora.date(),
        Agendamento.data <= limite.date(),
    ).all()

    for agendamento in agendamentos_proximos:
        notificacao_existente = Notificacao.query.filter_by(
            agendamento_id=agendamento.id,
            lida=False,
        ).first()
        if not notificacao_existente:
            mensagem = (
                f"Lembrete: Você tem um agendamento para {agendamento.laboratorio} em "
                f"{agendamento.data.strftime('%d/%m/%Y')}"
            )
            nova_notificacao = Notificacao(
                usuario_id=agendamento.usuario_id,
                agendamento_id=agendamento.id,
                mensagem=mensagem,
            )
            db.session.add(nova_notificacao)

    try:
        db.session.commit()
        return True
    except SQLAlchemyError as e:
        db.session.rollback()
        handle_internal_error(e)
        return False
