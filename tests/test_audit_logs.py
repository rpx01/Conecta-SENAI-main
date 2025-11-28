from datetime import date
from conecta_senai.models.audit_log import AuditLog


def test_audit_log_criacao_e_atualizacao(client, login_admin, app):
    token, _ = login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/agendamentos",
        json={
            "data": date.today().isoformat(),
            "laboratorio": "LabAudit",
            "turma": "1A",
            "turno": "Manhã",
            "horarios": ["08:00"],
        },
        headers=headers,
    )
    assert resp.status_code == 201
    ag_id = resp.get_json()["id"]

    update_resp = client.put(
        f"/api/agendamentos/{ag_id}",
        json={"turma": "1B"},
        headers=headers,
    )
    assert update_resp.status_code == 200

    with app.app_context():
        creates = AuditLog.query.filter_by(entity="Agendamento", entity_id=ag_id, action="create").all()
        updates = AuditLog.query.filter_by(entity="Agendamento", entity_id=ag_id, action="update").all()
        assert len(creates) == 1
        assert len(updates) == 1
