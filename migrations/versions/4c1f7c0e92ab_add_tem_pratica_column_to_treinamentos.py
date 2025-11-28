"""add tem_pratica column to treinamentos

Revision ID: 4c1f7c0e92ab
Revises: 25108d2d85b5
Create Date: 2025-07-22 17:18:27.331963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c1f7c0e92ab'
down_revision: Union[str, Sequence[str], None] = '25108d2d85b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'tem_pratica' not in columns:
        op.add_column('treinamentos', sa.Column('tem_pratica', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'tem_pratica' in columns:
        op.drop_column('treinamentos', 'tem_pratica')
