"""create inscricoes_treinamento_portal table

Revision ID: aa0b6b279d7c
Revises: e5a1fcf7485d
Create Date: 2024-08-21 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'aa0b6b279d7c'
down_revision: Union[str, Sequence[str], None] = 'e5a1fcf7485d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'inscricoes_treinamento_portal',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('treinamento_id', sa.Integer(), nullable=True),
        sa.Column('nome_treinamento', sa.String(length=255), nullable=False),
        sa.Column('matricula', sa.String(length=50), nullable=False),
        sa.Column('tipo_treinamento', sa.String(length=100), nullable=False),
        sa.Column('nome_completo', sa.String(length=255), nullable=False),
        sa.Column('naturalidade', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('data_nascimento', sa.Date(), nullable=False),
        sa.Column('cpf', sa.String(length=14), nullable=False),
        sa.Column('empresa', sa.String(length=255), nullable=False),
        sa.Column('criado_em', sa.DateTime(), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('inscricoes_treinamento_portal')
