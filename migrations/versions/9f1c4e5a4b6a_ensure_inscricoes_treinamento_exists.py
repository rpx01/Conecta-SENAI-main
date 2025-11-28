"""ensure inscricoes_treinamento table exists

Revision ID: 9f1c4e5a4b6a
Revises: be93033c7a1c
Create Date: 2025-08-22 12:30:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '9f1c4e5a4b6a'
down_revision: Union[str, Sequence[str], None] = 'be93033c7a1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS inscricoes_treinamento (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
            turma_id INTEGER NOT NULL REFERENCES turmas_treinamento(id),
            nome VARCHAR(150) NOT NULL,
            email VARCHAR(150) NOT NULL,
            cpf VARCHAR(20) NOT NULL,
            data_nascimento DATE,
            empresa VARCHAR(150),
            data_inscricao TIMESTAMP
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS inscricoes_treinamento")
