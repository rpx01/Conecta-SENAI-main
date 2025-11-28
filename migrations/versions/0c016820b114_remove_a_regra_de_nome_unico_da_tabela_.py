"""Remove a regra de nome unico da tabela de treinamentos

Revision ID: 0c016820b114
Revises: 6ed67839f494
Create Date: 2025-07-23 21:33:54.598726

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c016820b114'
down_revision = '6ed67839f494'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tenta remover a constraint de nome único. Se não existir, ignora o erro.
    try:
        with op.batch_alter_table('treinamentos', schema=None) as batch_op:
            # O nome da constraint no PostgreSQL é geralmente 'tabela_coluna_key'
            batch_op.drop_constraint('treinamentos_nome_key', type_='unique')
    except Exception as e:
        print("Constraint 'treinamentos_nome_key' não encontrada, possivelmente já foi removida. Ignorando.")
        print(e)


def downgrade() -> None:
    # Recria a constraint se for necessário reverter a migração
    with op.batch_alter_table('treinamentos', schema=None) as batch_op:
        batch_op.create_unique_constraint('treinamentos_nome_key', ['nome'])
