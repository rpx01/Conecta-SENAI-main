import pytest


@pytest.mark.usefixtures("app")
def test_criar_e_atualizar_horario_basedados(client):
    # Cria novo horário
    resp = client.post(
        "/api/horarios",
        json={"nome": "08:00 as 10:00", "turno": "Manhã"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["turno"] == "Manhã"
    horario_id = data["id"]

    # Atualiza o turno do horário
    resp = client.put(
        f"/api/horarios/{horario_id}",
        json={"nome": "08:00 as 10:00", "turno": "Tarde"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["turno"] == "Tarde"

    # Confirma persistência
    resp = client.get("/api/horarios")
    assert resp.status_code == 200
    itens = resp.get_json()
    assert any(h["id"] == horario_id and h["turno"] == "Tarde" for h in itens)
