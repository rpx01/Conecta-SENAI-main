"""Utilitários compartilhados para as rotas do módulo de suporte de TI."""
from __future__ import annotations

import logging
from typing import Iterable

from flask import current_app
from sqlalchemy import inspect, text
from sqlalchemy.exc import ProgrammingError

from conecta_senai.models import db
from conecta_senai.models.suporte_chamado import SuporteChamado


LOGGER = logging.getLogger(__name__)


def ensure_tables_exist(models: Iterable[type[db.Model]]) -> None:
    """Garante que as tabelas (e colunas críticas) existam antes do uso.

    Esta função mantém a compatibilidade com ambientes onde as migrações
    ainda não foram aplicadas totalmente. Além de criar tabelas ausentes,
    ela verifica e cria as colunas ``observacoes``, ``local_unidade`` e
    ``nome_solicitante`` da tabela de chamados e garante que ``user_id`` aceite
    ``NULL``, reproduzindo o comportamento esperado das migrações oficiais.
    """

    inspector = inspect(db.engine)
    for model in models:
        table_name = model.__tablename__
        if not inspector.has_table(table_name):
            model.__table__.create(db.engine)
            inspector = inspect(db.engine)

        if table_name == SuporteChamado.__tablename__:
            inspector = _ensure_suporte_chamados_columns(inspector)


def _ensure_suporte_chamados_columns(inspector):
    """Garante que colunas críticas existam na tabela de chamados."""

    table_name = SuporteChamado.__tablename__
    columns_info = inspector.get_columns(table_name)
    columns = {column["name"] for column in columns_info}
    ddl_statements: list[tuple] = []

    if "observacoes" not in columns:
        ddl_statements.append(
            (
                text("ALTER TABLE suporte_chamados ADD COLUMN observacoes TEXT"),
                "Adicionada coluna observacoes em suporte_chamados.",
            )
        )

    if "local_unidade" not in columns:
        ddl_statements.append(
            (
                text(
                    "ALTER TABLE suporte_chamados ADD COLUMN local_unidade VARCHAR(150)"
                ),
                "Adicionada coluna local_unidade em suporte_chamados.",
            )
        )

    if "nome_solicitante" not in columns:
        ddl_statements.append(
            (
                text(
                    "ALTER TABLE suporte_chamados ADD COLUMN nome_solicitante VARCHAR(150)"
                ),
                "Adicionada coluna nome_solicitante em suporte_chamados.",
            )
        )

    if "inicio_atendimento_at" not in columns:
        ddl_statements.append(
            (
                text(
                    "ALTER TABLE suporte_chamados ADD COLUMN inicio_atendimento_at TIMESTAMP"
                ),
                "Adicionada coluna inicio_atendimento_at em suporte_chamados.",
            )
        )

    if "encerrado_at" not in columns:
        ddl_statements.append(
            (
                text(
                    "ALTER TABLE suporte_chamados ADD COLUMN encerrado_at TIMESTAMP"
                ),
                "Adicionada coluna encerrado_at em suporte_chamados.",
            )
        )

    for ddl, message in ddl_statements:
        _execute_ddl(ddl, message)

    if ddl_statements:
        inspector = inspect(db.engine)
        columns_info = inspector.get_columns(table_name)

    user_column = next(
        (column for column in columns_info if column["name"] == "user_id"),
        None,
    )
    if user_column and not user_column.get("nullable", True):
        inspector = _make_user_id_nullable()

    return inspector


def _get_logger():
    try:  # pragma: no cover - logger cai no app em produção
        return current_app.logger
    except RuntimeError:  # fora do contexto da aplicação (ex.: testes)
        return LOGGER


def _execute_ddl(ddl, success_message: str) -> None:
    try:
        with db.engine.begin() as connection:
            connection.execute(ddl)
            _get_logger().info(success_message)
    except ProgrammingError as exc:  # pragma: no cover - dependente do banco
        mensagem = str(exc).lower()
        if "duplicate column" not in mensagem and "already exists" not in mensagem:
            raise


def _make_user_id_nullable():
    dialect = db.engine.dialect.name
    table_name = SuporteChamado.__tablename__

    if dialect == "sqlite":
        _recreate_table_with_nullable_user()
    else:
        ddl = text(
            f"ALTER TABLE {table_name} ALTER COLUMN user_id DROP NOT NULL"
        )
        _execute_ddl(
            ddl,
            "Alterada coluna user_id de suporte_chamados para aceitar valores nulos.",
        )
    return inspect(db.engine)


def _recreate_table_with_nullable_user() -> None:
    """Recria a tabela garantindo ``user_id`` como nullable no SQLite."""

    table_name = SuporteChamado.__tablename__
    old_table = f"{table_name}_old"
    column_names = [column.name for column in SuporteChamado.__table__.columns]
    columns_csv = ", ".join(column_names)

    with db.engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=OFF"))
        connection.execute(text(f"ALTER TABLE {table_name} RENAME TO {old_table}"))
        SuporteChamado.__table__.create(bind=connection)
        connection.execute(
            text(
                f"INSERT INTO {table_name} ({columns_csv}) "
                f"SELECT {columns_csv} FROM {old_table}"
            )
        )
        connection.execute(text(f"DROP TABLE {old_table}"))
        connection.execute(text("PRAGMA foreign_keys=ON"))

    _get_logger().info(
        "Recriada tabela suporte_chamados no SQLite para permitir user_id nulo."
    )
