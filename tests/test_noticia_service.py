"""Testes para o módulo de regras de negócio de notícias."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import current_app
from sqlalchemy import text
from sqlalchemy.orm.attributes import LoaderCallableStatus
from werkzeug.datastructures import FileStorage

from conecta_senai.models import db
from conecta_senai.models.noticia import Noticia
from conecta_senai.schemas.noticia import NoticiaSchema
from conecta_senai.services import noticia_service


def test_atualizar_noticia_cria_tabela_imagens_quando_ausente(app, tmp_path):
    """Garante que a tabela de imagens é criada automaticamente e o binário é persistido."""

    with app.app_context():
        with db.engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS imagens_noticias"))

        noticia_service._TABELA_IMAGENS_DISPONIVEL = None

        noticia = Noticia(titulo="Titulo teste", conteudo="Conteudo teste")
        db.session.add(noticia)
        db.session.commit()

        current_app.static_folder = tmp_path.as_posix()

        arquivo = FileStorage(
            stream=io.BytesIO(b"dados"),
            filename="imagem.png",
            content_type="image/png",
        )

        noticia = Noticia.query.get(noticia.id)
        atualizada = noticia_service.atualizar_noticia(noticia, {}, arquivo)

        assert noticia_service._TABELA_IMAGENS_DISPONIVEL is True
        assert atualizada.imagem is not None
        assert atualizada.imagem.tem_conteudo is True
        assert atualizada.imagem.conteudo == b"dados"
        assert atualizada.imagem.content_type == "image/png"

        assert atualizada.imagem_url is not None
        assert atualizada.imagem.url_publica.startswith("/api/noticias/imagens/")

        serializada = NoticiaSchema().dump(atualizada)
        assert serializada["imagem_url"].startswith("/api/noticias/imagens/")

        caminho_relativo = atualizada.imagem.caminho_relativo
        caminho_final = Path(current_app.static_folder) / caminho_relativo

        assert caminho_final.exists()

        estado_relacionamento = db.inspect(atualizada).attrs.imagem.loaded_value
        assert estado_relacionamento is not LoaderCallableStatus.NO_VALUE


def test_imagem_persistida_fica_disponivel_apos_redeploy(app, tmp_path):
    """Garante que o binário permanece acessível mesmo após remover o arquivo físico."""

    with app.app_context():
        db.create_all()

        noticia_service._TABELA_IMAGENS_DISPONIVEL = None

        current_app.static_folder = tmp_path.as_posix()

        noticia = Noticia(titulo="Notícia com imagem", conteudo="Conteúdo de teste")
        db.session.add(noticia)
        db.session.commit()

        arquivo = FileStorage(
            stream=io.BytesIO(b"conteudo-imagem"),
            filename="imagem.jpg",
            content_type="image/jpeg",
        )

        noticia = db.session.get(Noticia, noticia.id)
        atualizada = noticia_service.atualizar_noticia(noticia, {}, arquivo)

        assert atualizada.imagem is not None
        assert atualizada.imagem.conteudo == b"conteudo-imagem"
        assert atualizada.imagem.content_type == "image/jpeg"

        url = atualizada.imagem.url_publica
        assert url.startswith("/api/noticias/imagens/")

        caminho = Path(current_app.static_folder) / atualizada.imagem.caminho_relativo
        assert caminho.exists()
        caminho.unlink()
        assert not caminho.exists()

        client = app.test_client()
        resposta = client.get(url)

        assert resposta.status_code == 200
        assert resposta.data == b"conteudo-imagem"
        assert resposta.mimetype == "image/jpeg"

def test_publicar_noticias_agendadas_altera_status_para_ativo(app):
    with app.app_context():
        db.create_all()

        agora = datetime.now(timezone.utc)
        noticia_agendada = Noticia(
            titulo="Notícia agendada",
            conteudo="Conteúdo agendado para publicação automática." * 1,
            ativo=False,
            data_publicacao=agora - timedelta(minutes=10),
        )
        noticia_futura = Noticia(
            titulo="Notícia futura",
            conteudo="Conteúdo ainda não deve ser publicado automaticamente." * 1,
            ativo=False,
            data_publicacao=agora + timedelta(minutes=10),
        )

        db.session.add_all([noticia_agendada, noticia_futura])
        db.session.commit()

        resultado = noticia_service.publicar_noticias_agendadas()

        publicada = db.session.get(Noticia, noticia_agendada.id)
        pendente = db.session.get(Noticia, noticia_futura.id)

        assert resultado == {"total": 1, "publicadas": 1, "falhas": 0}
        assert publicada.ativo is True
        assert pendente.ativo is False


def test_remover_destaques_expirados_considera_dias_uteis(app):
    with app.app_context():
        db.create_all()

        agora = datetime.now(timezone.utc)
        noticia_expirada = Noticia(
            titulo="Notícia expirada",
            conteudo="Conteúdo",  # noqa: E501 - texto simplificado
            destaque=True,
            data_publicacao=agora - timedelta(days=10),
        )
        noticia_recente = Noticia(
            titulo="Notícia recente",
            conteudo="Conteúdo",
            destaque=True,
            data_publicacao=agora - timedelta(days=1),
        )

        db.session.add_all([noticia_expirada, noticia_recente])
        db.session.commit()

        resultado = noticia_service.remover_destaques_expirados()

        expirada = db.session.get(Noticia, noticia_expirada.id)
        recente = db.session.get(Noticia, noticia_recente.id)

        assert resultado == {"total": 2, "ajustados": 1, "falhas": 0}
        assert expirada.destaque is False
        assert recente.destaque is True


def test_criar_noticia_persiste_data_evento(app):
    with app.app_context():
        db.create_all()

        dados = {
            "titulo": "Notícia com evento",
            "resumo": "Resumo com tamanho adequado.",
            "conteudo": "Conteúdo extenso o suficiente para ser válido no cadastro.",
            "marcar_calendario": True,
            "data_publicacao": datetime(2024, 4, 10, tzinfo=timezone.utc),
            "data_evento": datetime(2024, 5, 5, tzinfo=timezone.utc),
        }

        noticia = noticia_service.criar_noticia(dados)

        assert noticia.marcar_calendario is True
        esperado_naive = dados["data_evento"].replace(tzinfo=None)
        assert noticia.data_evento is not None
        assert noticia.data_evento.replace(tzinfo=None) == esperado_naive

        recuperada = db.session.get(Noticia, noticia.id)
        assert recuperada is not None
        assert recuperada.data_evento is not None
        assert recuperada.data_evento.replace(tzinfo=None) == esperado_naive
