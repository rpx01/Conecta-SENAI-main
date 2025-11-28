"""Ensure teoria_online column exists on turmas_treinamento

Revision ID: c53b7353ca16
Revises: 1c02b7a6da56
Create Date: 2024-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c53b7353ca16'
down_revision: Union[str, Sequence[str], None] = '1c02b7a6da56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add teoria_online column if missing."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("turmas_treinamento")]
    if "teoria_online" not in columns:
        op.add_column(
            "turmas_treinamento",
            sa.Column("teoria_online", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.alter_column("turmas_treinamento", "teoria_online", server_default=None)


def downgrade() -> None:
    """Remove teoria_online column if present."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("turmas_treinamento")]
    if "teoria_online" in columns:
        op.drop_column("turmas_treinamento", "teoria_online")
