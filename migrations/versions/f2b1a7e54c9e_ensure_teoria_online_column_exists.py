"""Ensure teoria_online column exists on turmas_treinamento

Revision ID: f2b1a7e54c9e
Revises: aecabea0aca8
Create Date: 2025-09-11 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f2b1a7e54c9e'
down_revision: Union[str, Sequence[str], None] = 'aecabea0aca8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add coluna teoria_online se nao existir."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [
        col["name"] for col in inspector.get_columns("turmas_treinamento")
    ]
    if "teoria_online" not in columns:
        op.add_column(
            "turmas_treinamento",
            sa.Column(
                "teoria_online",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
        op.alter_column(
            "turmas_treinamento", "teoria_online", server_default=None
        )


def downgrade() -> None:
    """Remove coluna teoria_online se existir."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [
        col["name"] for col in inspector.get_columns("turmas_treinamento")
    ]
    if "teoria_online" in columns:
        op.drop_column("turmas_treinamento", "teoria_online")
