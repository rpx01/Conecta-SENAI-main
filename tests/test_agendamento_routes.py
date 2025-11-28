from datetime import date, timedelta

def test_criar_e_listar_agendamento(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/agendamentos', json={
        'data': date.today().isoformat(),
        'laboratorio': 'Lab1',
        'turma': '1A',
        'turno': 'Manhã',
        'horarios': ['08:00', '09:00']
    }, headers=headers)
    assert resp.status_code == 201
    ag_id = resp.get_json()['id']

    resp = client.get(f'/api/agendamentos/{ag_id}', headers=headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['laboratorio'] == 'Lab1'

    resp = client.get('/api/agendamentos', headers=headers)
    assert resp.status_code == 200
    ags = resp.get_json()
    assert any(a['id'] == ag_id for a in ags)


def test_criar_agendamento_dados_incompletos(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post('/api/agendamentos', json={
        'data': date.today().isoformat(),
        'turma': '1A',
        'turno': 'Manhã',
        'horarios': ['08:00']
    }, headers=headers)
    assert resp.status_code == 400


def test_atualizar_agendamento_data_invalida(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    r = client.post('/api/agendamentos', json={
        'data': date.today().isoformat(),
        'laboratorio': 'LabX',
        'turma': '1B',
        'turno': 'Manhã',
        'horarios': ['08:00']
    }, headers=headers)
    ag_id = r.get_json()['id']
    resp = client.put(f'/api/agendamentos/{ag_id}', json={'data': '2023-02-30'}, headers=headers)
    assert resp.status_code == 400


def test_verificar_disponibilidade_e_conflitos(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}

    hoje = date.today()

    # Cria agendamento inicial
    resp_create = client.post('/api/agendamentos', json={
        'data': hoje.isoformat(),
        'laboratorio': 'LabDisp',
        'turma': '1C',
        'turno': 'Manhã',
        'horarios': ['08:00', '09:00']
    }, headers=headers)
    assert resp_create.status_code == 201
    ag_id = resp_create.get_json()['id']

    # Consulta disponibilidade para o mesmo período
    resp_check = client.get('/api/agendamentos/verificar-disponibilidade', query_string={
        'data': hoje.isoformat(),
        'laboratorio': 'LabDisp',
        'turno': 'Manhã'
    }, headers=headers)
    assert resp_check.status_code == 200
    dados = resp_check.get_json()
    assert 'horarios_reservados' in dados
    assert 'laboratorio_id' in dados
    assert '08:00' in dados['horarios_reservados']

    # Consulta disponibilidade em data diferente (deve estar livre)
    resp_livre = client.get('/api/agendamentos/verificar-disponibilidade', query_string={
        'data': (hoje + timedelta(days=1)).isoformat(),
        'laboratorio': 'LabDisp',
        'turno': 'Manhã'
    }, headers=headers)
    assert resp_livre.status_code == 200
    dados_livres = resp_livre.get_json()
    assert dados_livres['horarios_reservados'] == []

    # Tenta criar agendamento parcialmente sobreposto
    resp_conf = client.post('/api/agendamentos', json={
        'data': hoje.isoformat(),
        'laboratorio': 'LabDisp',
        'turma': '1D',
        'turno': 'Manhã',
        'horarios': ['09:00', '10:00']
    }, headers=headers)
    assert resp_conf.status_code == 409
    dados_conf = resp_conf.get_json()
    assert 'conflitos' in dados_conf
    assert dados_conf['conflitos']


def test_admin_remove_agendamento(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}
    resp = client.post(
        '/api/agendamentos',
        json={
            'data': date.today().isoformat(),
            'laboratorio': 'LabDel',
            'turma': '2A',
            'turno': 'Manhã',
            'horarios': ['08:00']
        },
        headers=headers,
    )
    ag_id = resp.get_json()['id']

    del_resp = client.delete(f'/api/agendamentos/{ag_id}', headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.get_json()['mensagem'] == 'Agendamento removido com sucesso'


def test_delete_agendamento_non_owner_forbidden(client, non_admin_auth_headers, login_admin):
    token, _ = login_admin(client)
    admin_headers = {'Authorization': f'Bearer {token}'}
    resp = client.post(
        '/api/agendamentos',
        json={
            'data': date.today().isoformat(),
            'laboratorio': 'LabDel2',
            'turma': '2B',
            'turno': 'Manhã',
            'horarios': ['08:00']
        },
        headers=admin_headers,
    )
    ag_id = resp.get_json()['id']

    resp_forbidden = client.delete(
        f'/api/agendamentos/{ag_id}',
        headers=non_admin_auth_headers,
    )
    assert resp_forbidden.status_code == 403


def test_non_admin_crud_own_agendamento(client, non_admin_auth_headers):
    headers = non_admin_auth_headers

    create_resp = client.post(
        '/api/agendamentos',
        json={
            'data': date.today().isoformat(),
            'laboratorio': 'LabUser',
            'turma': '1X',
            'turno': 'Manhã',
            'horarios': ['08:00']
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    ag_id = create_resp.get_json()['id']

    update_resp = client.put(
        f'/api/agendamentos/{ag_id}',
        json={'turma': '1Y'},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.get_json()['turma'] == '1Y'

    delete_resp = client.delete(f'/api/agendamentos/{ag_id}', headers=headers)
    assert delete_resp.status_code == 200


def test_non_admin_update_other_forbidden(client, login_admin, non_admin_auth_headers):
    token, _ = login_admin(client)
    admin_headers = {'Authorization': f'Bearer {token}'}

    resp = client.post(
        '/api/agendamentos',
        json={
            'data': date.today().isoformat(),
            'laboratorio': 'LabOut',
            'turma': '3A',
            'turno': 'Manhã',
            'horarios': ['08:00']
        },
        headers=admin_headers,
    )
    ag_id = resp.get_json()['id']

    resp_forbidden = client.put(
        f'/api/agendamentos/{ag_id}',
        json={'turma': '3B'},
        headers=non_admin_auth_headers,
    )
    assert resp_forbidden.status_code == 403
