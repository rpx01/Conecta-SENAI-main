"""add_teoria_online_to_turmas_treinamento

Revision ID: 760a497b44b6
Revises: c53b7353ca16
Create Date: 2025-09-11 17:28:49.529303

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '760a497b44b6'
down_revision: Union[str, Sequence[str], None] = 'c53b7353ca16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add teoria_online column to turmas_treinamento."""
    op.add_column(
        "turmas_treinamento",
        sa.Column(
            "teoria_online", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")
        ),
    )
    op.alter_column("turmas_treinamento", "teoria_online", server_default=None)


def downgrade() -> None:
    """Remove teoria_online column."""
    op.drop_column("turmas_treinamento", "teoria_online")
