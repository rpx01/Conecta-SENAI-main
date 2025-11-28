"""ensure data_treinamento_pratico exists on turmas_treinamento

Revision ID: be93033c7a1c
Revises: bfad9cd914dc
Create Date: 2025-08-22 12:20:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'be93033c7a1c'
down_revision: Union[str, Sequence[str], None] = 'bfad9cd914dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('turmas_treinamento')]
    if 'data_treinamento_pratico' not in columns:
        op.add_column('turmas_treinamento', sa.Column('data_treinamento_pratico', sa.Date(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('turmas_treinamento')]
    if 'data_treinamento_pratico' in columns:
        op.drop_column('turmas_treinamento', 'data_treinamento_pratico')
