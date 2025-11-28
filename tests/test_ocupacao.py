import os
import sys
from datetime import date, datetime, timedelta
import jwt

import pytest
from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from conecta_senai.models import db
from conecta_senai.models.sala import Sala
from conecta_senai.models.user import User
from conecta_senai.models.ocupacao import Ocupacao
from conecta_senai.routes.ocupacao import ocupacao_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    db.init_app(app)
    app.register_blueprint(ocupacao_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()
        user = User(
            nome='Test',
            email='test@example.com',
            senha='Password1!',
            tipo='admin'
        )
        db.session.add(user)
        sala = Sala(nome='Sala Teste', capacidade=10)
        db.session.add(sala)
        db.session.commit()
    return app

@pytest.fixture
def client(app):
    return app.test_client()


def test_listar_ocupacoes_retorna_json(client, app):
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()
    token = jwt.encode(
        {
            "user_id": user.id,
            "nome": user.nome,
            "perfil": user.tipo,
            "exp": datetime.utcnow() + timedelta(hours=1),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    client.post(
        "/api/ocupacoes",
        json={
            "sala_id": sala.id,
            "curso_evento": "Teste",
            "data_inicio": date.today().isoformat(),
            "data_fim": date.today().isoformat(),
            "turno": "Manhã",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = client.get("/api/ocupacoes", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    dados = resp.get_json()
    assert isinstance(dados, list)
    assert all(isinstance(item, dict) for item in dados)


def test_verificar_disponibilidade(client, app):
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()
        sala_id = sala.id
    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    response = client.get(
        '/api/ocupacoes/verificar-disponibilidade',
        query_string={
            'sala_id': sala_id,
            'data_inicio': date.today().strftime('%Y-%m-%d'),
            'data_fim': date.today().strftime('%Y-%m-%d'),
            'turno': 'Manhã'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert set(data.keys()) == {'disponivel', 'sala', 'conflitos'}
    assert data['disponivel'] is True
    assert data['conflitos'] == []
    assert data['sala']['id'] == sala_id


def test_excluir_ocupacao_periodo(client, app):
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()

    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    data_inicio = date.today()
    data_fim = data_inicio + timedelta(days=2)

    resp = client.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Curso Teste',
        'data_inicio': data_inicio.isoformat(),
        'data_fim': data_fim.isoformat(),
        'turno': 'Manhã'
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 201
    ocupacoes = resp.get_json()
    assert len(ocupacoes) == 3

    primeiro_id = ocupacoes[0]['id']
    grupo_id = ocupacoes[0]['grupo_ocupacao_id']

    resp_del = client.delete(f'/api/ocupacoes/{primeiro_id}', headers={'Authorization': f'Bearer {token}'})
    assert resp_del.status_code == 200
    resultado = resp_del.get_json()
    assert resultado['removidas'] == 3

    with app.app_context():
        restantes = Ocupacao.query.filter_by(grupo_ocupacao_id=grupo_id).all()
        assert restantes == []


def test_obter_ocupacao_periodo_completo(client, app):
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()

    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    data_inicio = date.today()
    data_fim = data_inicio + timedelta(days=2)

    resp = client.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Curso Teste',
        'data_inicio': data_inicio.isoformat(),
        'data_fim': data_fim.isoformat(),
        'turno': 'Manhã'
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 201
    ocupacoes = resp.get_json()
    assert len(ocupacoes) == 3

    qualquer_id = ocupacoes[1]['id']

    resp_get = client.get(f'/api/ocupacoes/{qualquer_id}', headers={'Authorization': f'Bearer {token}'})
    assert resp_get.status_code == 200
    dados = resp_get.get_json()
    assert dados['data_inicio'] == data_inicio.isoformat()
    assert dados['data_fim'] == data_fim.isoformat()


def test_verificar_disponibilidade_edicao_ignora_registro(client, app):
    """Ao editar uma ocupação, a verificação deve ignorar o próprio grupo."""
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()

    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    data_inicio = date.today()
    data_fim = data_inicio + timedelta(days=2)

    resp = client.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Curso Teste',
        'data_inicio': data_inicio.isoformat(),
        'data_fim': data_fim.isoformat(),
        'turno': 'Manhã'
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 201
    ocupacoes = resp.get_json()
    ocupacao_id = ocupacoes[1]['id']

    resp_check = client.get('/api/ocupacoes/verificar-disponibilidade', query_string={
        'sala_id': sala.id,
        'data_inicio': data_inicio.isoformat(),
        'data_fim': data_fim.isoformat(),
        'turno': 'Manhã',
        'ocupacao_id': ocupacao_id
    }, headers={'Authorization': f'Bearer {token}'})

    assert resp_check.status_code == 200
    resultado = resp_check.get_json()
    assert resultado['disponivel'] is True


def test_tendencia_ocupacoes_endpoint(client, app):
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()
    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    client.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Evento',
        'data_inicio': date.today().isoformat(),
        'data_fim': date.today().isoformat(),
        'turno': 'Manhã'
    }, headers={'Authorization': f'Bearer {token}'})

    resp = client.get('/api/ocupacoes/tendencia', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    dados = resp.get_json()
    assert isinstance(dados, list)


def test_calendario_ocupacoes_cor_por_turno(client, app):
    """Verifica se o endpoint de calendário colore conforme o turno."""
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()

    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    hoje = date.today()

    resp = client.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Teste de Cor',
        'data_inicio': hoje.isoformat(),
        'data_fim': hoje.isoformat(),
        'turno': 'Noite'
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 201

    resp_cal = client.get('/api/ocupacoes/calendario', query_string={
        'data_inicio': hoje.isoformat(),
        'data_fim': hoje.isoformat()
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp_cal.status_code == 200
    eventos = resp_cal.get_json()
    assert len(eventos) == 1
    evento = eventos[0]
    assert evento['backgroundColor'] == '#512DA8'
    assert evento['borderColor'] == '#512DA8'
    assert evento['extendedProps']['turno'] == 'Noite'


def test_resumo_periodo_endpoint(client, app):
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()

    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    hoje = date.today()

    client.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Resumo',
        'data_inicio': hoje.isoformat(),
        'data_fim': hoje.isoformat(),
        'turno': 'Manhã'
    }, headers={'Authorization': f'Bearer {token}'})

    resp = client.get('/api/ocupacoes/resumo-periodo', query_string={
        'data_inicio': hoje.isoformat(),
        'data_fim': hoje.isoformat()
    }, headers={'Authorization': f'Bearer {token}'})

    assert resp.status_code == 200
    resumo = resp.get_json()
    assert hoje.isoformat() in resumo
    dia = resumo[hoje.isoformat()]
    assert 'Manhã' in dia
    assert dia['Manhã']['ocupadas'] == 1


def test_criar_ocupacao_dados_incompletos(client, app):
    with app.app_context():
        user = User.query.first()
    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    resp = client.post('/api/ocupacoes', json={
        'curso_evento': 'Curso',
        'data_inicio': date.today().isoformat(),
        'data_fim': date.today().isoformat(),
        'turno': 'Manhã'
    }, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 400


def test_atualizar_ocupacao_turno_invalido(client, app):
    with app.app_context():
        user = User.query.first()
        sala = Sala.query.first()
    token = jwt.encode({
        'user_id': user.id,
        'nome': user.nome,
        'perfil': user.tipo,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    r = client.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Evento',
        'data_inicio': date.today().isoformat(),
        'data_fim': date.today().isoformat(),
        'turno': 'Manhã'
    }, headers={'Authorization': f'Bearer {token}'})
    ocupacao_id = r.get_json()[0]['id']
    resp = client.put(f'/api/ocupacoes/{ocupacao_id}', json={'turno': 'X'}, headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 400
