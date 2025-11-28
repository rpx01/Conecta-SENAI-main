from __future__ import with_statement

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from conecta_senai import create_app
from conecta_senai.extensions import db

config = context.config
fileConfig(config.config_file_name)

app = create_app()
with app.app_context():
    target_metadata = db.metadata
    db_url = os.getenv("DATABASE_URL") or app.config.get("SQLALCHEMY_DATABASE_URI")
    if db_url:
        config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
