"""ensure data_termino exists on turmas_treinamento

Revision ID: bfad9cd914dc
Revises: 64b22f54fe47
Create Date: 2025-08-22 12:15:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'bfad9cd914dc'
down_revision: Union[str, Sequence[str], None] = '64b22f54fe47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('turmas_treinamento')]
    if 'data_termino' not in columns:
        op.add_column('turmas_treinamento', sa.Column('data_termino', sa.Date(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('turmas_treinamento')]
    if 'data_termino' in columns:
        op.drop_column('turmas_treinamento', 'data_termino')
