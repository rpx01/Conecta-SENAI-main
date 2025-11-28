"""ensure extra columns exist on treinamentos table

Revision ID: c68944a9fc4a
Revises: da712fed38d7
Create Date: 2025-08-22 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c68944a9fc4a'
down_revision: Union[str, Sequence[str], None] = 'da712fed38d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'tem_pratica' not in columns:
        op.add_column('treinamentos', sa.Column('tem_pratica', sa.Boolean(), nullable=True))
    if 'links_materiais' not in columns:
        op.add_column('treinamentos', sa.Column('links_materiais', sa.JSON(), nullable=True))
    if 'data_criacao' not in columns:
        op.add_column('treinamentos', sa.Column('data_criacao', sa.DateTime(), nullable=True))
    if 'data_atualizacao' not in columns:
        op.add_column('treinamentos', sa.Column('data_atualizacao', sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'data_atualizacao' in columns:
        op.drop_column('treinamentos', 'data_atualizacao')
    if 'data_criacao' in columns:
        op.drop_column('treinamentos', 'data_criacao')
    if 'links_materiais' in columns:
        op.drop_column('treinamentos', 'links_materiais')
    if 'tem_pratica' in columns:
        op.drop_column('treinamentos', 'tem_pratica')

