import jwt
from datetime import datetime, timedelta


def admin_headers(app):
    with app.app_context():
        from conecta_senai.models.user import User
        user = User.query.filter_by(email="admin@example.com").first()
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
        return {"Authorization": f"Bearer {token}"}


def test_crud_contatos_secretaria(client, app):
    headers = admin_headers(app)
    # Criação
    resp = client.post(
        "/api/treinamentos/secretaria",
        json={"nome": "João", "email": "joao@example.com"},
        headers=headers,
    )
    assert resp.status_code == 201
    contato_id = resp.get_json()["id"]

    # Listagem
    resp = client.get("/api/treinamentos/secretaria", headers=headers)
    assert resp.status_code == 200
    dados = resp.get_json()
    assert any(c["email"] == "joao@example.com" for c in dados)

    # Atualização
    resp = client.put(
        f"/api/treinamentos/secretaria/{contato_id}",
        json={"nome": "João Silva", "email": "joao@example.com"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.get_json()["nome"] == "João Silva"

    # Exclusão
    resp = client.delete(
        f"/api/treinamentos/secretaria/{contato_id}", headers=headers
    )
    assert resp.status_code == 200


def test_criar_contato_email_duplicado(client, app):
    headers = admin_headers(app)
    payload = {"nome": "Maria", "email": "maria@example.com"}
    r1 = client.post(
        "/api/treinamentos/secretaria", json=payload, headers=headers
    )
    assert r1.status_code == 201
    r2 = client.post(
        "/api/treinamentos/secretaria", json=payload, headers=headers
    )
    assert r2.status_code == 409


def test_rotas_requerem_admin(client, non_admin_auth_headers):
    # Sem token
    resp = client.get("/api/treinamentos/secretaria")
    assert resp.status_code == 401
    # Usuário comum
    resp = client.post(
        "/api/treinamentos/secretaria",
        json={"nome": "Ana", "email": "ana@example.com"},
        headers=non_admin_auth_headers,
    )
    assert resp.status_code == 403
