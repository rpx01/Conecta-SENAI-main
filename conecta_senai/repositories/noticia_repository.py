"""Repositório com operações de banco para notícias."""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from conecta_senai.models import db
from conecta_senai.models.noticia import Noticia


log = logging.getLogger(__name__)


class NoticiaRepository:
    """Encapsula o acesso ao banco para o modelo :class:`Noticia`."""

    _table_checked: bool = False

    @classmethod
    def ensure_table_exists(cls, force_refresh: bool = False) -> bool:
        """Garante que a tabela de notícias esteja disponível.

        Em ambientes recém configurados as migrações podem não ter sido
        executadas, o que provocaria erros de ``ProgrammingError`` em todas as
        requisições. Para manter a API funcional garantimos que a tabela seja
        criada dinamicamente caso ainda não exista.
        """

        if cls._table_checked and not force_refresh:
            return True

        engine = db.engine
        inspector = inspect(engine)
        if inspector.has_table(Noticia.__tablename__):
            cls._ensure_marcar_calendario_column(engine, inspector)
            cls._ensure_data_evento_column(engine, inspector)
            cls._table_checked = True
            return True

        try:
            Noticia.__table__.create(engine)
            log.info("Tabela 'noticias' criada automaticamente por ausência prévia.")
        except SQLAlchemyError:
            cls._table_checked = False
            log.exception("Falha ao criar a tabela 'noticias'.")
            raise

        cls._table_checked = True
        return True

    @classmethod
    def _ensure_marcar_calendario_column(cls, engine, inspector) -> None:
        """Garante a existência da coluna ``marcar_calendario``.

        Ambientes que ainda não executaram a migração correspondente lançam
        erros de ``UndefinedColumn`` ao consultar o modelo ``Noticia``. Para
        garantir retrocompatibilidade, criamos a coluna dinamicamente quando
        ela ainda não está presente na tabela.
        """

        table_name = Noticia.__tablename__
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "marcar_calendario" in columns:
            return

        default_literal = "false"
        if engine.dialect.name == "sqlite":
            # SQLite não reconhece ``false`` como literal booleano.
            default_literal = "0"

        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN marcar_calendario BOOLEAN "
                        f"NOT NULL DEFAULT {default_literal}"
                    )
                )
            log.info(
                "Coluna 'marcar_calendario' criada automaticamente na tabela 'noticias'."
            )
        except SQLAlchemyError:
            cls._table_checked = False
            log.exception(
                "Falha ao atualizar a tabela 'noticias' com a coluna 'marcar_calendario'."
            )
            raise

    @classmethod
    def _ensure_data_evento_column(cls, engine, inspector) -> None:
        """Garante a existência da coluna ``data_evento``."""

        table_name = Noticia.__tablename__
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "data_evento" in columns:
            return

        column_type = "TIMESTAMP WITH TIME ZONE"
        if engine.dialect.name == "sqlite":
            column_type = "DATETIME"

        try:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} "
                        f"ADD COLUMN data_evento {column_type}"
                    )
                )
            log.info("Coluna 'data_evento' criada automaticamente na tabela 'noticias'.")
        except SQLAlchemyError:
            cls._table_checked = False
            log.exception(
                "Falha ao atualizar a tabela 'noticias' com a coluna 'data_evento'.",
            )
            raise

    @staticmethod
    def base_query():
        NoticiaRepository.ensure_table_exists()
        return Noticia.query

    @staticmethod
    def get_by_id(noticia_id: int) -> Optional[Noticia]:
        NoticiaRepository.ensure_table_exists()
        return db.session.get(Noticia, noticia_id)

    @staticmethod
    def add(noticia: Noticia) -> Noticia:
        NoticiaRepository.ensure_table_exists()
        db.session.add(noticia)
        db.session.commit()
        return noticia

    @staticmethod
    def delete(noticia: Noticia) -> None:
        NoticiaRepository.ensure_table_exists()
        db.session.delete(noticia)
        db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def rollback():  # pragma: no cover - utilitário para fluxos de erro
        db.session.rollback()

    @staticmethod
    def save(noticia: Noticia) -> Noticia:
        NoticiaRepository.ensure_table_exists()
        try:
            db.session.add(noticia)
            db.session.commit()
            return noticia
        except SQLAlchemyError:
            db.session.rollback()
            raise
