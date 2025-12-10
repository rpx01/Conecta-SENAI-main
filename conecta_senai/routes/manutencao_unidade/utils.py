from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy import inspect

from conecta_senai.models import db

LOGGER = logging.getLogger(__name__)


def ensure_tables_exist(models: Iterable[type[db.Model]]) -> None:
    """Garante que as tabelas necessárias existam para o módulo de manutenção.

    A função cria tabelas ausentes quando as migrações ainda não foram
    aplicadas, preservando compatibilidade em ambientes legados.
    """

    inspector = inspect(db.engine)
    for model in models:
        table_name = model.__tablename__
        if not inspector.has_table(table_name):
            LOGGER.info("Criando tabela ausente: %s", table_name)
            model.__table__.create(db.engine)
            inspector = inspect(db.engine)
