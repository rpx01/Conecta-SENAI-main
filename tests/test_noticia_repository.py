from sqlalchemy import inspect, text

from conecta_senai.models import db
from conecta_senai.models.noticia import Noticia
from conecta_senai.repositories.noticia_repository import NoticiaRepository


def _drop_noticias_table(engine):
    inspector = inspect(engine)
    if inspector.has_table(Noticia.__tablename__):
        Noticia.__table__.drop(engine)


def _create_legacy_table_without_data_evento(engine):
    table_name = Noticia.__tablename__
    with engine.begin() as connection:
        connection.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        connection.execute(
            text(
                """
                CREATE TABLE noticias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo VARCHAR(200) NOT NULL,
                    resumo VARCHAR(500),
                    conteudo TEXT NOT NULL,
                    autor VARCHAR(120),
                    imagem_url VARCHAR(500),
                    destaque BOOLEAN NOT NULL DEFAULT 0,
                    ativo BOOLEAN NOT NULL DEFAULT 1,
                    marcar_calendario BOOLEAN NOT NULL DEFAULT 0,
                    data_publicacao DATETIME
                )
                """
            )
        )


def test_ensure_table_exists_creates_table_when_missing(app):
    with app.app_context():
        engine = db.engine
        _drop_noticias_table(engine)

        inspector = inspect(engine)
        assert not inspector.has_table(Noticia.__tablename__)

        assert NoticiaRepository.ensure_table_exists(force_refresh=True)
        assert inspect(engine).has_table(Noticia.__tablename__)


def test_add_after_automatic_table_creation(app):
    with app.app_context():
        engine = db.engine
        _drop_noticias_table(engine)
        NoticiaRepository.ensure_table_exists(force_refresh=True)

        noticia = Noticia(titulo="Titulo", conteudo="Conteudo")
        criada = NoticiaRepository.add(noticia)

        assert criada.id is not None
        assert inspect(engine).has_table(Noticia.__tablename__)


def test_ensure_table_exists_adds_data_evento_column(app):
    with app.app_context():
        engine = db.engine
        _create_legacy_table_without_data_evento(engine)

        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns(Noticia.__tablename__)}
        assert "data_evento" not in columns

        NoticiaRepository.ensure_table_exists(force_refresh=True)

        inspector = inspect(engine)
        columns = {column["name"] for column in inspector.get_columns(Noticia.__tablename__)}
        assert "data_evento" in columns
