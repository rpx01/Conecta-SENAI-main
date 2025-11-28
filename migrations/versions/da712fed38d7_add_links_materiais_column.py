"""add links_materiais column to treinamentos

Revision ID: da712fed38d7
Revises: 4c1f7c0e92ab
Create Date: 2025-07-22 18:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'da712fed38d7'
down_revision: Union[str, Sequence[str], None] = '4c1f7c0e92ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'links_materiais' not in columns:
        op.add_column('treinamentos', sa.Column('links_materiais', sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'links_materiais' in columns:
        op.drop_column('treinamentos', 'links_materiais')
