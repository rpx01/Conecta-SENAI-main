"""rename data_termino column to data_fim

Revision ID: 67c822ca4b6e
Revises: 9f1c4e5a4b6a
Create Date: 2025-08-22 12:45:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '67c822ca4b6e'
down_revision: Union[str, Sequence[str], None] = '9f1c4e5a4b6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("turmas_treinamento")]
    if "data_termino" in columns and "data_fim" not in columns:
        with op.batch_alter_table("turmas_treinamento") as batch_op:
            batch_op.alter_column("data_termino", new_column_name="data_fim")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("turmas_treinamento")]
    if "data_fim" in columns and "data_termino" not in columns:
        with op.batch_alter_table("turmas_treinamento") as batch_op:
            batch_op.alter_column("data_fim", new_column_name="data_termino")
