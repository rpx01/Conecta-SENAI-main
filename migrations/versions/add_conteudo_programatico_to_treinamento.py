from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5e78c8e1a7b9"
down_revision: Union[str, Sequence[str], None] = "47aff0d3be81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "treinamentos", sa.Column("conteudo_programatico", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("treinamentos", "conteudo_programatico")
