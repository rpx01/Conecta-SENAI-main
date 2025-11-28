"""add status column to turmas_treinamento

Revision ID: 47aff0d3be81
Revises: 67c822ca4b6e
Create Date: 2025-08-22 13:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '47aff0d3be81'
down_revision: Union[str, Sequence[str], None] = '67c822ca4b6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('turmas_treinamento')]
    if 'status' not in columns:
        op.add_column('turmas_treinamento', sa.Column('status', sa.String(length=20), nullable=False, server_default='aberta'))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('turmas_treinamento')]
    if 'status' in columns:
        op.drop_column('turmas_treinamento', 'status')
