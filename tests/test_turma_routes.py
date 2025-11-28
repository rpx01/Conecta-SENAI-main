


def test_criar_e_atualizar_turma(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}

    resp = client.post('/api/turmas', json={'nome': 'Turma1'}, headers=headers)
    assert resp.status_code == 201
    turma_id = resp.get_json()['id']

    resp_up = client.put(f'/api/turmas/{turma_id}', json={'nome': 'TurmaX'}, headers=headers)
    assert resp_up.status_code == 200
    assert resp_up.get_json()['nome'] == 'TurmaX'

    resp_get = client.get(f'/api/turmas/{turma_id}', headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.get_json()['nome'] == 'TurmaX'


def test_atualizar_turma_nome_duplicado(client, login_admin):
    token, _ = login_admin(client)
    headers = {'Authorization': f'Bearer {token}'}

    client.post('/api/turmas', json={'nome': 'A'}, headers=headers)
    r2 = client.post('/api/turmas', json={'nome': 'B'}, headers=headers)
    turma_b = r2.get_json()['id']

    resp = client.put(f'/api/turmas/{turma_b}', json={'nome': 'A'}, headers=headers)
    assert resp.status_code == 400
