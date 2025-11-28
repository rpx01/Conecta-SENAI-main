from datetime import datetime, timedelta, timezone

from datetime import datetime, timedelta, timezone

from conecta_senai.models import db
from conecta_senai.models.noticia import Noticia


def _criar_noticia(**kwargs):
    noticia = Noticia(**kwargs)
    db.session.add(noticia)
    db.session.commit()
    return noticia


def test_listar_noticias_filtra_calendario_true(client, app):
    with app.app_context():
        agora = datetime.now(timezone.utc)
        destaque_calendario = _criar_noticia(
            titulo="Evento A",
            conteudo="Conteúdo do evento A",
            resumo="Resumo A",
            ativo=True,
            data_publicacao=agora - timedelta(days=1),
            marcar_calendario=True,
            data_evento=agora + timedelta(days=5),
        )
        _criar_noticia(
            titulo="Notícia comum",
            conteudo="Conteúdo comum",
            resumo="Resumo comum",
            ativo=True,
            data_publicacao=agora,
            marcar_calendario=False,
        )
        destaque_calendario_id = destaque_calendario.id

    resposta = client.get('/api/noticias?marcar_calendario=true&per_page=10')
    assert resposta.status_code == 200
    dados = resposta.get_json()
    ids = [item['id'] for item in dados['items']]
    assert ids == [destaque_calendario_id]
    assert dados['items'][0]['marcar_calendario'] is True
    assert dados['items'][0]['data_evento'] is not None


def test_listar_noticias_filtra_calendario_false(client, app):
    with app.app_context():
        agora = datetime.now(timezone.utc)
        noticia_true = _criar_noticia(
            titulo="Evento marcado",
            conteudo="Conteúdo com evento",
            resumo="Resumo evento",
            ativo=True,
            data_publicacao=agora,
            marcar_calendario=True,
            data_evento=agora + timedelta(days=10),
        )
        noticia_false = _criar_noticia(
            titulo="Notícia sem calendário",
            conteudo="Conteúdo sem evento",
            resumo="Resumo sem evento",
            ativo=True,
            data_publicacao=agora - timedelta(days=2),
            marcar_calendario=False,
        )
        noticia_true_id = noticia_true.id
        noticia_false_id = noticia_false.id

    resposta = client.get('/api/noticias?marcar_calendario=false&per_page=10')
    assert resposta.status_code == 200
    dados = resposta.get_json()
    ids = [item['id'] for item in dados['items']]
    assert noticia_true_id not in ids
    assert noticia_false_id in ids
    assert all(item['marcar_calendario'] is False for item in dados['items'])
