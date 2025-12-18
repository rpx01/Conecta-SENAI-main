from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1d2d74c8a7b"
down_revision: Union[str, Sequence[str], None] = "e5b8e9f1a2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "inscricoes_treinamento", sa.Column("nota_teoria", sa.Float(), nullable=True)
    )
    op.add_column(
        "inscricoes_treinamento", sa.Column("nota_pratica", sa.Float(), nullable=True)
    )
    op.add_column(
        "inscricoes_treinamento",
        sa.Column("status_aprovacao", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("inscricoes_treinamento", "status_aprovacao")
    op.drop_column("inscricoes_treinamento", "nota_pratica")
    op.drop_column("inscricoes_treinamento", "nota_teoria")
