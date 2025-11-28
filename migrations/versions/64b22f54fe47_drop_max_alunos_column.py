"""drop obsolete max_alunos column

Revision ID: 64b22f54fe47
Revises: c68944a9fc4a
Create Date: 2025-07-22 18:52:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '64b22f54fe47'
down_revision: Union[str, Sequence[str], None] = 'c68944a9fc4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'max_alunos' in columns:
        op.drop_column('treinamentos', 'max_alunos')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c['name'] for c in inspector.get_columns('treinamentos')]
    if 'max_alunos' not in columns:
        op.add_column('treinamentos', sa.Column('max_alunos', sa.Integer(), nullable=False, server_default='20'))
        op.alter_column('treinamentos', 'max_alunos', server_default=None)
