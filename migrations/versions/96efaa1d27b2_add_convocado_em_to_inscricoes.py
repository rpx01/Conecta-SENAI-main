from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "96efaa1d27b2"
down_revision: Union[str, Sequence[str], None] = "760a497b44b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "inscricoes_treinamento",
        sa.Column("convocado_em", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("inscricoes_treinamento", "convocado_em")
