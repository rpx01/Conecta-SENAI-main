from datetime import date

from conecta_senai.models import db
from conecta_senai.models.agendamento import Agendamento, Notificacao
from conecta_senai.models.user import User


def test_user_deletion_cascades_to_agendamentos_and_notificacoes(app):
    with app.app_context():
        usuario = User(
            nome='Cascade User',
            email='cascade@example.com',
            senha='Senha@123',
            tipo='comum',
        )
        db.session.add(usuario)
        db.session.commit()

        agendamento = Agendamento(
            data=date.today(),
            laboratorio='Laboratório 1',
            turma='Turma A',
            turno='manha',
            horarios=['08:00'],
            usuario_id=usuario.id,
        )
        usuario.agendamentos.append(agendamento)
        db.session.add(agendamento)
        db.session.commit()

        notificacao_usuario = Notificacao(
            usuario_id=usuario.id, mensagem='Aviso direto ao usuário'
        )
        notificacao_agendamento = Notificacao(
            usuario_id=usuario.id,
            mensagem='Aviso vinculado ao agendamento',
            agendamento_id=agendamento.id,
        )
        agendamento.notificacoes.append(notificacao_agendamento)
        usuario.notificacoes.extend([notificacao_usuario, notificacao_agendamento])
        db.session.add_all([notificacao_usuario, notificacao_agendamento])
        db.session.commit()

        db.session.delete(usuario)
        db.session.commit()

        assert db.session.get(User, usuario.id) is None
        assert Agendamento.query.filter_by(usuario_id=usuario.id).count() == 0
        assert Notificacao.query.filter_by(usuario_id=usuario.id).count() == 0
        assert Notificacao.query.filter_by(agendamento_id=agendamento.id).count() == 0
