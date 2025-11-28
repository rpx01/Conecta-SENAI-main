import jwt
from datetime import datetime, timedelta


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


def test_criar_treinamento_nome_repetido_permitido(client, app):
    headers = admin_headers(app)
    resp1 = client.post('/api/treinamentos/catalogo', json={'nome': 'Treino', 'codigo': 'T1'}, headers=headers)
    assert resp1.status_code == 201
    resp2 = client.post('/api/treinamentos/catalogo', json={'nome': 'Treino', 'codigo': 'T2'}, headers=headers)
    assert resp2.status_code == 201


def test_criar_treinamento_nome_codigo_iguais_falha(client, app):
    headers = admin_headers(app)
    client.post('/api/treinamentos/catalogo', json={'nome': 'TreinoX', 'codigo': 'TX'}, headers=headers)
    resp = client.post('/api/treinamentos/catalogo', json={'nome': 'TreinoX', 'codigo': 'TX'}, headers=headers)
    assert resp.status_code == 400


def test_atualizar_treinamento_nome_duplicado_permitido(client, app):
    headers = admin_headers(app)
    client.post('/api/treinamentos/catalogo', json={'nome': 'A', 'codigo': 'C1'}, headers=headers)
    r2 = client.post('/api/treinamentos/catalogo', json={'nome': 'B', 'codigo': 'C2'}, headers=headers)
    tid2 = r2.get_json()['id']
    resp = client.put(f'/api/treinamentos/catalogo/{tid2}', json={'nome': 'A'}, headers=headers)
    assert resp.status_code == 200


def test_atualizar_turma_ativa_permitido(client, app):
    headers = admin_headers(app)
    r = client.post('/api/treinamentos/catalogo', json={'nome': 'Trein', 'codigo': 'T99'}, headers=headers)
    treino_id = r.get_json()['id']

    hoje = datetime.utcnow().date()
    resp_turma = client.post(
        '/api/treinamentos/turmas',
        json={
            'treinamento_id': treino_id,
            'data_inicio': (hoje - timedelta(days=1)).isoformat(),
            'data_fim': (hoje + timedelta(days=1)).isoformat(),
        },
        headers=headers,
    )
    assert resp_turma.status_code == 201
    turma_id = resp_turma.get_json()['id']

    resp_up = client.put(
        f'/api/treinamentos/turmas/{turma_id}',
        json={'local_realizacao': 'Nova'},
        headers=headers,
    )
    assert resp_up.status_code == 200
    assert resp_up.get_json()['local_realizacao'] == 'Nova'
