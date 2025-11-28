"""add convocado_em to inscricoes

Revision ID: 96efaa1d27b2
Revises: 760a497b44b6
Create Date: 2025-09-11 18:27:48.741197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96efaa1d27b2'
down_revision: Union[str, Sequence[str], None] = '760a497b44b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add column convocado_em to inscricoes_treinamento."""
    op.add_column(
        "inscricoes_treinamento",
        sa.Column("convocado_em", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Remove column convocado_em."""
    op.drop_column("inscricoes_treinamento", "convocado_em")
