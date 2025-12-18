from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1c02b7a6da56"
down_revision: Union[str, Sequence[str], None] = "f2b1a7e54c9e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("turmas_treinamento")]
    if "teoria_online" not in columns:
        op.add_column(
            "turmas_treinamento",
            sa.Column(
                "teoria_online", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
        )
        op.alter_column("turmas_treinamento", "teoria_online", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("turmas_treinamento")]
    if "teoria_online" in columns:
        op.drop_column("turmas_treinamento", "teoria_online")
