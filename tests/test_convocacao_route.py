from datetime import date, datetime, timedelta
import jwt

from conecta_senai.models import db, Treinamento, TurmaTreinamento, InscricaoTreinamento


def admin_headers(app):
    with app.app_context():
        from conecta_senai.models.user import User
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode(
            {'user_id': user.id, 'nome': user.nome, 'perfil': user.tipo, 'exp': datetime.utcnow() + timedelta(hours=1)},
            app.config['SECRET_KEY'], algorithm='HS256'
        )
        return {'Authorization': f'Bearer {token}'}


def test_convocar_inscrito(client, app, monkeypatch):
    headers = admin_headers(app)
    with app.app_context():
        treino = Treinamento(nome='Treino', codigo='T1', carga_horaria=8, tem_pratica=True)
        db.session.add(treino)
        db.session.commit()
        turma = TurmaTreinamento(
            treinamento_id=treino.id,
            data_inicio=date.today(),
            data_fim=date.today(),
            local_realizacao='Local',
            horario='08h',
            teoria_online=True,
        )
        db.session.add(turma)
        db.session.commit()
        inscricao = InscricaoTreinamento(
            turma_id=turma.id,
            nome='João',
            email='joao@example.com',
            cpf='123',
            empresa='Empresa'
        )
        db.session.add(inscricao)
        db.session.commit()
        iid = inscricao.id

    called = {}

    def fake_send_email(to, subject, html):
        called['to'] = to
        called['subject'] = subject
        called['html'] = html

    monkeypatch.setattr('conecta_senai.routes.treinamentos.treinamento.send_email', fake_send_email)

    resp = client.post(f'/api/inscricoes/{iid}/convocar', headers=headers)
    assert resp.status_code == 200
    assert called['to'] == 'joao@example.com'
    assert 'Convocação' in called['subject']
    with app.app_context():
        insc = db.session.get(InscricaoTreinamento, iid)
        assert insc.convocado_em is not None
