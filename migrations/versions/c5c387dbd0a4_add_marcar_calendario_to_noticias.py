"""add marcar_calendario column to noticias table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5c387dbd0a4"
down_revision: Union[str, Sequence[str], None] = "8bfad4c51c4a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLE_NAME = "noticias"
COLUMN_NAME = "marcar_calendario"
DEFAULT_VALUE = sa.text("false")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table(TABLE_NAME):
        return

    columns = {column["name"] for column in inspector.get_columns(TABLE_NAME)}
    if COLUMN_NAME in columns:
        return

    op.add_column(
        TABLE_NAME,
        sa.Column(
            COLUMN_NAME,
            sa.Boolean(),
            nullable=False,
            server_default=DEFAULT_VALUE,
        ),
    )
    op.execute(
        sa.text(
            f"UPDATE {TABLE_NAME} SET {COLUMN_NAME} = false WHERE {COLUMN_NAME} IS NULL"
        )
    )
    op.alter_column(
        TABLE_NAME,
        COLUMN_NAME,
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=DEFAULT_VALUE,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table(TABLE_NAME):
        return

    columns = {column["name"] for column in inspector.get_columns(TABLE_NAME)}
    if COLUMN_NAME not in columns:
        return

    op.drop_column(TABLE_NAME, COLUMN_NAME)
