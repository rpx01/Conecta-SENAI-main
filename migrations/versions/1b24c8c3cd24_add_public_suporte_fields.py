"""Add fields to support public ticket creation"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '1b24c8c3cd24'
down_revision: Union[str, Sequence[str], None] = 'aecabea0aca8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('suporte_chamados', 'user_id', existing_type=sa.Integer(), nullable=True)
    op.add_column('suporte_chamados', sa.Column('nome_solicitante', sa.String(length=150), nullable=True))
    op.add_column('suporte_chamados', sa.Column('local_unidade', sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column('suporte_chamados', 'local_unidade')
    op.drop_column('suporte_chamados', 'nome_solicitante')
    op.alter_column('suporte_chamados', 'user_id', existing_type=sa.Integer(), nullable=False)
