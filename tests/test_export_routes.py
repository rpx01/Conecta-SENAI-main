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
from conecta_senai.routes.user import user_bp
from conecta_senai.routes.laboratorios import agendamento_bp
from conecta_senai.routes.ocupacao import ocupacao_bp


@pytest.fixture
def app_agendamentos():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    db.init_app(app)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(agendamento_bp, url_prefix='/api')
    with app.app_context():
        db.create_all()
        admin = User(nome='Admin', email='admin@example.com', senha='Password1!', tipo='admin')
        db.session.add(admin)
        db.session.commit()
    return app


@pytest.fixture
def client_ag(app_agendamentos):
    return app_agendamentos.test_client()




def test_export_agendamentos_csv(client_ag, login_admin):
    token, _ = login_admin(client_ag)
    headers = {'Authorization': f'Bearer {token}'}
    client_ag.post('/api/agendamentos', json={
        'data': date.today().isoformat(),
        'laboratorio': 'Lab',
        'turma': '1A',
        'turno': 'Manhã',
        'horarios': ['08:00']
    }, headers=headers)
    resp = client_ag.get('/api/agendamentos/export?formato=csv', headers=headers)
    assert resp.status_code == 200
    assert 'text/csv' in resp.content_type


def test_export_agendamentos_pdf(client_ag, login_admin):
    token, _ = login_admin(client_ag)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client_ag.get('/api/agendamentos/export?formato=pdf', headers=headers)
    assert resp.status_code == 200
    assert 'application/pdf' in resp.content_type


def test_export_agendamentos_xlsx(client_ag, login_admin):
    token, _ = login_admin(client_ag)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client_ag.get('/api/agendamentos/export?formato=xlsx', headers=headers)
    assert resp.status_code == 200
    assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in resp.content_type


@pytest.fixture
def app_ocupacoes():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    db.init_app(app)
    app.register_blueprint(ocupacao_bp, url_prefix='/api')
    with app.app_context():
        db.create_all()
        user = User(nome='Admin', email='admin@example.com', senha='Password1!', tipo='admin')
        sala = Sala(nome='Sala', capacidade=10)
        db.session.add_all([user, sala])
        db.session.commit()
    return app


@pytest.fixture
def client_oc(app_ocupacoes):
    return app_ocupacoes.test_client()


def gerar_token(app):
    with app.app_context():
        user = User.query.first()
        return jwt.encode({
            'user_id': user.id,
            'nome': user.nome,
            'perfil': user.tipo,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')


def test_export_ocupacoes_csv(client_oc, app_ocupacoes):
    token = gerar_token(app_ocupacoes)
    headers = {'Authorization': f'Bearer {token}'}
    with app_ocupacoes.app_context():
        sala = Sala.query.first()
    client_oc.post('/api/ocupacoes', json={
        'sala_id': sala.id,
        'curso_evento': 'Evento',
        'data_inicio': date.today().isoformat(),
        'data_fim': date.today().isoformat(),
        'turno': 'Manhã'
    }, headers=headers)
    resp = client_oc.get('/api/ocupacoes/export?formato=csv', headers=headers)
    assert resp.status_code == 200
    assert 'text/csv' in resp.content_type


def test_export_ocupacoes_pdf(client_oc, app_ocupacoes):
    token = gerar_token(app_ocupacoes)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client_oc.get('/api/ocupacoes/export?formato=pdf', headers=headers)
    assert resp.status_code == 200
    assert 'application/pdf' in resp.content_type


def test_export_ocupacoes_xlsx(client_oc, app_ocupacoes):
    token = gerar_token(app_ocupacoes)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client_oc.get('/api/ocupacoes/export?formato=xlsx', headers=headers)
    assert resp.status_code == 200
    assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in resp.content_type

