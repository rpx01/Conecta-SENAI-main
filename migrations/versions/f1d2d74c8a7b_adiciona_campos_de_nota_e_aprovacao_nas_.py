"""adiciona campos de nota e aprovacao nas inscricoes

Revision ID: f1d2d74c8a7b
Revises: e5b8e9f1a2c3
Create Date: 2025-07-24 12:57:28.788241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f1d2d74c8a7b'
down_revision: Union[str, Sequence[str], None] = 'e5b8e9f1a2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('inscricoes_treinamento', sa.Column('nota_teoria', sa.Float(), nullable=True))
    op.add_column('inscricoes_treinamento', sa.Column('nota_pratica', sa.Float(), nullable=True))
    op.add_column('inscricoes_treinamento', sa.Column('status_aprovacao', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('inscricoes_treinamento', 'status_aprovacao')
    op.drop_column('inscricoes_treinamento', 'nota_pratica')
    op.drop_column('inscricoes_treinamento', 'nota_teoria')
