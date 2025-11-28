import jwt
from datetime import datetime, timedelta, date
from unittest.mock import patch

from conecta_senai.models import db
from conecta_senai.models.instrutor import Instrutor
from conecta_senai.models.secretaria_treinamentos import SecretariaTreinamentos
from conecta_senai.models.treinamento import Treinamento, TurmaTreinamento
from conecta_senai.services.email_service import notificar_atualizacao_turma


def coletar_destinatarios(mock_send):
    destinatarios = []
    for call in mock_send.call_args_list:
        if call.args:
            to = call.args[0]
        else:
            to = call.kwargs.get('to', [])
        if isinstance(to, str):
            destinatarios.append(to)
        else:
            destinatarios.extend(to)
    return destinatarios


def admin_headers(app):
    with app.app_context():
        from conecta_senai.models.user import User
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode({
            'user_id': user.id,
            'nome': user.nome,
            'perfil': user.tipo,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}


def test_notificar_nova_turma_enviada(client, app):
    headers = admin_headers(app)
    resp = client.post(
        '/api/treinamentos/catalogo',
        json={'nome': 'T', 'codigo': 'C1'},
        headers=headers,
    )
    treino_id = resp.get_json()['id']
    with app.app_context():
        inst = Instrutor(nome='Inst', email='inst@example.com')
        sec = SecretariaTreinamentos(nome='Sec', email='sec@example.com')
        db.session.add_all([inst, sec])
        db.session.commit()
        inst_id = inst.id
    hoje = date.today()
    payload = {
        'treinamento_id': treino_id,
        'data_inicio': hoje.isoformat(),
        'data_fim': (hoje + timedelta(days=1)).isoformat(),
        'instrutor_id': inst_id,
    }
    with patch('conecta_senai.services.email_service.send_email') as mock_send:
        r = client.post(
            '/api/treinamentos/turmas',
            json=payload,
            headers=headers,
        )
        assert r.status_code == 201  # nosec B101
        destinatarios = set(coletar_destinatarios(mock_send))
        assert 'inst@example.com' in destinatarios  # nosec B101
        assert 'sec@example.com' in destinatarios  # nosec B101


def test_atualizar_turma_genera_diff(client, app):
    headers = admin_headers(app)
    r = client.post(
        '/api/treinamentos/catalogo',
        json={'nome': 'T2', 'codigo': 'C2'},
        headers=headers,
    )
    treino_id = r.get_json()['id']
    with app.app_context():
        inst = Instrutor(nome='I', email='i@example.com')
        db.session.add(inst)
        db.session.commit()
        inst_id = inst.id
    hoje = date.today()
    resp = client.post(
        '/api/treinamentos/turmas',
        json={
            'treinamento_id': treino_id,
            'data_inicio': hoje.isoformat(),
            'data_fim': (hoje + timedelta(days=1)).isoformat(),
            'local_realizacao': 'A',
            'instrutor_id': inst_id,
        },
        headers=headers,
    )
    turma_id = resp.get_json()['id']
    novo_inicio = hoje + timedelta(days=1)
    with patch(
        'conecta_senai.routes.treinamentos.treinamento.notificar_atualizacao_turma'
    ) as mock_notify:
        resp_up = client.put(
            f'/api/treinamentos/turmas/{turma_id}',
            json={
                'data_inicio': novo_inicio.isoformat(),
                'local_realizacao': 'B',
            },
            headers=headers,
        )
        assert resp_up.status_code == 200  # nosec B101
        assert mock_notify.called  # nosec B101
        diff = mock_notify.call_args[0][1]
        assert diff['data_inicio'] == (
            hoje.strftime('%d/%m/%Y'),
            novo_inicio.strftime('%d/%m/%Y'),
        )  # nosec B101
        assert diff['local_realizacao'] == ('A', 'B')  # nosec B101


def test_notificar_atualizacao_envia_emails_instrutores(app):
    with app.app_context():
        treino = Treinamento(nome='T3', codigo='C3')
        inst_old = Instrutor(nome='Old', email='old@example.com')
        inst_new = Instrutor(nome='New', email='new@example.com')
        turma = TurmaTreinamento(
            treinamento=treino,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=1),
            instrutor=inst_new,
        )
        sec = SecretariaTreinamentos(nome='Sec2', email='sec2@example.com')
        db.session.add_all([treino, inst_old, inst_new, turma, sec])
        db.session.commit()
        diff = {'instrutor': (inst_old.nome, inst_new.nome)}
        with patch('conecta_senai.services.email_service.send_email') as mock_send:
            notificar_atualizacao_turma(turma, diff, inst_old)
            destinatarios = set(coletar_destinatarios(mock_send))
            assert destinatarios == {
                'sec2@example.com',
                'old@example.com',
                'new@example.com',
            }  # nosec B101


def test_notificar_atualizacao_instrutor_id(app):
    """Garante notificação ao instrutor antigo
    mesmo quando passado apenas o ID."""
    with app.app_context():
        treino = Treinamento(nome='T4', codigo='C4')
        inst_old = Instrutor(nome='Old2', email='old2@example.com')
        inst_new = Instrutor(nome='New2', email='new2@example.com')
        turma = TurmaTreinamento(
            treinamento=treino,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=1),
            instrutor=inst_new,
        )
        sec = SecretariaTreinamentos(nome='Sec3', email='sec3@example.com')
        db.session.add_all([treino, inst_old, inst_new, turma, sec])
        db.session.commit()
        diff = {'instrutor': (inst_old.nome, inst_new.nome)}
        with patch('conecta_senai.services.email_service.send_email') as mock_send:
            notificar_atualizacao_turma(turma, diff, inst_old.id)
            destinatarios = set(coletar_destinatarios(mock_send))
            assert destinatarios == {
                'sec3@example.com',
                'old2@example.com',
                'new2@example.com',
            }  # nosec B101


def test_notificar_atualizacao_instrutor_inalterado_recebe_email(app):
    with app.app_context():
        treino = Treinamento(nome='T6', codigo='C6')
        instrutor = Instrutor(nome='Inst', email='inst@example.com')
        turma = TurmaTreinamento(
            treinamento=treino,
            data_inicio=date.today(),
            data_fim=date.today() + timedelta(days=1),
            instrutor=instrutor,
            local_realizacao='Local Atual',
        )
        sec = SecretariaTreinamentos(nome='Sec4', email='sec4@example.com')
        db.session.add_all([treino, instrutor, turma, sec])
        db.session.commit()

        diff = {'local_realizacao': ('Local Antigo', 'Local Atual')}

        with patch('conecta_senai.services.email_service.send_email') as mock_send:
            notificar_atualizacao_turma(turma, diff, instrutor)

        destinatarios = coletar_destinatarios(mock_send)
        assert 'inst@example.com' in destinatarios  # nosec B101
        assert destinatarios.count('inst@example.com') == 1  # nosec B101


def test_atualizar_turma_notifica_instrutor_uma_vez(client, app):
    headers = admin_headers(app)
    r = client.post(
        '/api/treinamentos/catalogo',
        json={'nome': 'T5', 'codigo': 'C5'},
        headers=headers,
    )
    treino_id = r.get_json()['id']
    with app.app_context():
        inst_old = Instrutor(nome='Old', email='old@example.com')
        inst_new = Instrutor(nome='New', email='new@example.com')
        sec = SecretariaTreinamentos(nome='Sec', email='sec@example.com')
        db.session.add_all([inst_old, inst_new, sec])
        db.session.commit()
        old_id, new_id = inst_old.id, inst_new.id
    hoje = date.today()
    resp = client.post(
        '/api/treinamentos/turmas',
        json={
            'treinamento_id': treino_id,
            'data_inicio': hoje.isoformat(),
            'data_fim': (hoje + timedelta(days=1)).isoformat(),
            'instrutor_id': old_id,
        },
        headers=headers,
    )
    turma_id = resp.get_json()['id']
    patch_path = 'conecta_senai.services.email_service.send_nova_turma_instrutor_email'
    with (
        patch(patch_path) as mock_send,
        patch('conecta_senai.routes.treinamentos.treinamento.send_turma_alterada_email'),
        patch('conecta_senai.services.email_service.send_email'),
    ):
        r_up = client.put(
            f'/api/treinamentos/turmas/{turma_id}',
            json={'instrutor_id': new_id},
            headers=headers,
        )
        assert r_up.status_code == 200  # nosec B101
        assert mock_send.call_count == 1  # nosec B101


def test_remover_turma_envia_email_desmarcado(client, app):
    headers = admin_headers(app)
    resp = client.post(
        '/api/treinamentos/catalogo',
        json={'nome': 'TR', 'codigo': 'TR1'},
        headers=headers,
    )
    treino_id = resp.get_json()['id']

    with app.app_context():
        instrutor = Instrutor(nome='Instr', email='inst@example.com')
        secretaria = SecretariaTreinamentos(nome='Sec', email='sec@example.com')
        db.session.add_all([instrutor, secretaria])
        db.session.commit()
        instrutor_id = instrutor.id

    inicio = date.today() + timedelta(days=5)
    payload = {
        'treinamento_id': treino_id,
        'data_inicio': inicio.isoformat(),
        'data_fim': (inicio + timedelta(days=1)).isoformat(),
        'instrutor_id': instrutor_id,
    }
    turma_resp = client.post(
        '/api/treinamentos/turmas',
        json=payload,
        headers=headers,
    )
    turma_id = turma_resp.get_json()['id']

    with patch(
        'conecta_senai.routes.treinamentos.treinamento.send_treinamento_desmarcado_email'
    ) as mock_send:
        delete_resp = client.delete(
            f'/api/treinamentos/turmas/{turma_id}', headers=headers
        )
        assert delete_resp.status_code == 200  # nosec B101
        mock_send.assert_called_once()  # nosec B101
        recipients, turma_ctx = mock_send.call_args[0]
        assert {'sec@example.com', 'inst@example.com'} <= set(recipients)  # nosec B101
        assert turma_ctx.treinamento.nome == 'TR'  # nosec B101
