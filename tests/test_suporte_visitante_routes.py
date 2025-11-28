import pytest
from sqlalchemy import inspect, text

from conecta_senai.models import db
from conecta_senai.models.suporte_basedados import SuporteArea, SuporteTipoEquipamento
from conecta_senai.models.suporte_chamado import SuporteChamado
from conecta_senai.routes.suporte_ti.utils import ensure_tables_exist


@pytest.fixture
def suporte_base(app):
    with app.app_context():
        area = SuporteArea(nome='Infraestrutura')
        tipo = SuporteTipoEquipamento(nome='Notebook')
        db.session.add_all([area, tipo])
        db.session.commit()
        return {
            'area_nome': area.nome,
            'tipo_id': tipo.id,
        }


def test_abertura_chamado_limita_campos_texto(client, app, csrf_token, suporte_base):
    email = 'usuario.extenso.' + ('a' * 100) + '@example.com' + ('b' * 40)

    resposta = client.post(
        '/suporte/abrir-chamado',
        data={
            'csrf_token': csrf_token,
            'nome_completo': 'Visitante Teste',
            'email': email,
            'area': suporte_base['area_nome'],
            'tipo_equipamento_id': suporte_base['tipo_id'],
            'descricao_problema': 'Computador não liga.',
            'nivel_urgencia': 'Medio',
        },
    )

    assert resposta.status_code == 201
    payload = resposta.get_json()
    assert payload['mensagem']

    with app.app_context():
        chamado = SuporteChamado.query.get(payload['id'])
        email_max_len = SuporteChamado.email.property.columns[0].type.length
        area_max_len = SuporteChamado.area.property.columns[0].type.length
        assert len(chamado.email) == email_max_len
        assert len(chamado.area) <= area_max_len
        assert chamado.nivel_urgencia == 'Médio'


def test_abertura_chamado_token_invalido(client, suporte_base):
    resposta = client.post(
        '/suporte/abrir-chamado',
        data={
            'csrf_token': 'token-invalido',
            'nome_completo': 'Visitante Teste',
            'email': 'visitante@example.com',
            'area': suporte_base['area_nome'],
            'tipo_equipamento_id': suporte_base['tipo_id'],
            'descricao_problema': 'Sem acesso à rede.',
        },
    )

    assert resposta.status_code == 400
    assert resposta.get_json()['erro'] == 'Token CSRF inválido.'


def test_ensure_tables_exist_repairs_legacy_schema(
    client, app, csrf_token, suporte_base
):
    with app.app_context():
        with db.engine.begin() as connection:
            connection.execute(text('DROP TABLE IF EXISTS suporte_chamados'))
            connection.execute(
                text(
                    """
                    CREATE TABLE suporte_chamados (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        email VARCHAR(120) NOT NULL,
                        area VARCHAR(120) NOT NULL,
                        tipo_equipamento_id INTEGER NOT NULL,
                        patrimonio VARCHAR(120),
                        numero_serie VARCHAR(120),
                        descricao_problema TEXT NOT NULL,
                        nivel_urgencia VARCHAR(20) NOT NULL DEFAULT 'Baixo',
                        status VARCHAR(20) NOT NULL DEFAULT 'Aberto',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                    """
                )
            )

        ensure_tables_exist([SuporteChamado])
        inspector = inspect(db.engine)
        columns = inspector.get_columns('suporte_chamados')
        names = {column['name'] for column in columns}
        assert {'observacoes', 'local_unidade', 'nome_solicitante'} <= names
        user_column = next(col for col in columns if col['name'] == 'user_id')
        assert user_column['nullable'] is True

    resposta = client.post(
        '/suporte/abrir-chamado',
        data={
            'csrf_token': csrf_token,
            'nome_completo': 'Visitante Teste',
            'email': 'visitante@example.com',
            'area': suporte_base['area_nome'],
            'tipo_equipamento_id': suporte_base['tipo_id'],
            'descricao_problema': 'Falha geral.',
            'nivel_urgencia': 'Medio',
            'local_unidade': 'Unidade Centro',
        },
    )

    assert resposta.status_code == 201
    payload = resposta.get_json()
    with app.app_context():
        chamado = db.session.get(SuporteChamado, payload['id'])
        assert chamado is not None
        assert chamado.nome_solicitante == 'Visitante Teste'
        assert chamado.user_id is None
