"""create noticias table"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b36d3e0a3a9c'
down_revision: Union[str, Sequence[str], None] = 'c53b7353ca16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tabelas = inspector.get_table_names()

    if 'noticias' not in tabelas:
        op.create_table(
            'noticias',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('titulo', sa.String(length=200), nullable=False),
            sa.Column('resumo', sa.String(length=400), nullable=False),
            sa.Column('conteudo', sa.Text(), nullable=False),
            sa.Column('autor', sa.String(length=120), nullable=True),
            sa.Column('imagem_url', sa.String(length=500), nullable=True),
            sa.Column('destaque', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('data_publicacao', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_noticias_destaque', 'noticias', ['destaque'])
        op.create_index('ix_noticias_ativo', 'noticias', ['ativo'])
        op.create_index('ix_noticias_data_publicacao', 'noticias', ['data_publicacao'])
    else:
        colunas = {col['name'] for col in inspector.get_columns('noticias')}
        if 'destaque' not in colunas:
            op.add_column('noticias', sa.Column('destaque', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        if 'ativo' not in colunas:
            op.add_column('noticias', sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.text('true')))
        if 'data_publicacao' not in colunas:
            op.add_column('noticias', sa.Column('data_publicacao', sa.DateTime(), nullable=False, server_default=sa.func.now()))
        if 'criado_em' not in colunas:
            op.add_column('noticias', sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()))
        if 'atualizado_em' not in colunas:
            op.add_column('noticias', sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tabelas = inspector.get_table_names()

    if 'noticias' in tabelas:
        op.drop_index('ix_noticias_data_publicacao', table_name='noticias')
        op.drop_index('ix_noticias_ativo', table_name='noticias')
        op.drop_index('ix_noticias_destaque', table_name='noticias')
        op.drop_table('noticias')
