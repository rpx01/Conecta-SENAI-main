from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e417ea710acb"
down_revision: Union[str, Sequence[str], None] = "e7e8d9b51a4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "turmas_treinamento",
        sa.Column(
            "teoria_online",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("turmas_treinamento", "teoria_online", server_default=None)


def downgrade() -> None:
    op.drop_column("turmas_treinamento", "teoria_online")
