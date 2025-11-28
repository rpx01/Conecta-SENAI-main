import jwt
from datetime import datetime, timedelta
from conecta_senai.models.user import User


def admin_headers(app):
    with app.app_context():
        user = User.query.filter_by(email='admin@example.com').first()
        token = jwt.encode(
            {
                'user_id': user.id,
                'nome': user.nome,
                'perfil': user.tipo,
                'exp': datetime.utcnow() + timedelta(hours=1),
            },
            app.config['SECRET_KEY'],
            algorithm='HS256',
        )
        return {'Authorization': f'Bearer {token}'}


def test_delete_instrutor_as_non_admin_fails(client, app, non_admin_auth_headers):
    headers = admin_headers(app)
    resp = client.post('/api/instrutores', json={'nome': 'Instrutor'}, headers=headers)
    assert resp.status_code == 201
    instrutor_id = resp.get_json()['id']

    resp_del = client.delete(f'/api/instrutores/{instrutor_id}', headers=non_admin_auth_headers)
    assert resp_del.status_code == 403


def test_criar_instrutor_dados_incompletos(client, app):
    headers = admin_headers(app)
    resp = client.post('/api/instrutores', json={}, headers=headers)
    assert resp.status_code == 400
    assert 'erro' in resp.get_json()


def test_atualizar_instrutor_email_duplicado(client, app):
    headers = admin_headers(app)
    client.post('/api/instrutores', json={'nome': 'A', 'email': 'a@example.com'}, headers=headers)
    r2 = client.post('/api/instrutores', json={'nome': 'B', 'email': 'b@example.com'}, headers=headers)
    instrutor_b = r2.get_json()['id']
    resp = client.put(f'/api/instrutores/{instrutor_b}', json={'email': 'a@example.com'}, headers=headers)
    assert resp.status_code == 400



def test_atualizar_instrutor_parcial(client, app):
    headers = admin_headers(app)
    r = client.post('/api/instrutores', json={'nome': 'Edit'}, headers=headers)
    instrutor_id = r.get_json()['id']
    resp = client.put(f'/api/instrutores/{instrutor_id}', json={'nome': 'Novo'}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()['nome'] == 'Novo'

