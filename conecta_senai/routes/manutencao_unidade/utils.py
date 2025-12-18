from __future__ import annotations

import logging
from typing import Iterable

from sqlalchemy import inspect

from conecta_senai.models import db

LOGGER = logging.getLogger(__name__)


def ensure_tables_exist(models: Iterable[type[db.Model]]) -> None:
    inspector = inspect(db.engine)
    for model in models:
        table_name = model.__tablename__
        if not inspector.has_table(table_name):
            LOGGER.info("Criando tabela ausente: %s", table_name)
            model.__table__.create(db.engine)
            inspector = inspect(db.engine)
