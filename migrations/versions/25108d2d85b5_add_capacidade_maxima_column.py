"""add capacidade_maxima column to treinamentos

Revision ID: 25108d2d85b5
Revises: 933546544697
Create Date: 2025-07-22 12:30:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '25108d2d85b5'
down_revision: Union[str, Sequence[str], None] = '933546544697'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'capacidade_maxima' not in columns:
        op.add_column('treinamentos', sa.Column('capacidade_maxima', sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'capacidade_maxima' in columns:
        op.drop_column('treinamentos', 'capacidade_maxima')
