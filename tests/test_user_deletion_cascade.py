from datetime import date

from conecta_senai.models import db
from conecta_senai.models.agendamento import Agendamento, Notificacao
from conecta_senai.models.user import User


def test_user_deletion_cascades_to_agendamentos_and_notificacoes(app):
    with app.app_context():
        usuario = User(nome='Para Remover', email='remover@example.com', senha='Password1!')
        db.session.add(usuario)
        db.session.commit()

        agendamento = Agendamento(
            data=date.today(),
            laboratorio='Lab 1',
            turma='Turma A',
            turno='manha',
            horarios=['08:00-09:00'],
            usuario_id=usuario.id,
        )
        db.session.add(agendamento)
        db.session.commit()

        notificacao = Notificacao(
            usuario_id=usuario.id,
            mensagem='Teste de exclusão',
            agendamento_id=agendamento.id,
        )
        db.session.add(notificacao)
        db.session.commit()

        assert Agendamento.query.filter_by(usuario_id=usuario.id).count() == 1
        assert Notificacao.query.filter_by(usuario_id=usuario.id).count() == 1

        db.session.delete(usuario)
        db.session.commit()

        assert db.session.get(User, usuario.id) is None
        assert Agendamento.query.filter_by(usuario_id=usuario.id).count() == 0
        assert Notificacao.query.filter_by(usuario_id=usuario.id).count() == 0
        assert Notificacao.query.filter_by(agendamento_id=agendamento.id).count() == 0
