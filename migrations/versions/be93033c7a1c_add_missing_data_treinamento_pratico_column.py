from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "be93033c7a1c"
down_revision: Union[str, Sequence[str], None] = "bfad9cd914dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("turmas_treinamento")]
    if "data_treinamento_pratico" not in columns:
        op.add_column(
            "turmas_treinamento",
            sa.Column("data_treinamento_pratico", sa.Date(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [c["name"] for c in inspector.get_columns("turmas_treinamento")]
    if "data_treinamento_pratico" in columns:
        op.drop_column("turmas_treinamento", "data_treinamento_pratico")
