from urllib.parse import quote

from conecta_senai.models import db
from conecta_senai.models.log_rateio import LogLancamentoRateio


def test_listar_logs_rateio_paginado(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.get('/api/logs-rateio?page=1&per_page=5', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data['items']) == 5
    assert data['pages'] == 3

    resp2 = client.get('/api/logs-rateio?page=3&per_page=5', headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.get_json()
    assert len(data2['items']) == 5


def test_filtro_usuario_caracteres_especiais(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    usuario_especial = 'Usuário %Especial_'
    with client.application.app_context():
        log = LogLancamentoRateio(
            acao='create',
            usuario=usuario_especial,
            instrutor='Instrutor Teste',
            filial='F',
            uo='U',
            cr='CR',
            classe_valor='CL',
            percentual=10,
        )
        db.session.add(log)
        db.session.commit()
    resp = client.get(
        f"/api/logs-rateio?usuario={quote(usuario_especial)}&per_page=50",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(item['usuario'] == usuario_especial for item in data['items'])
