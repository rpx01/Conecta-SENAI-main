from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d204e2f154dd"
down_revision: Union[str, Sequence[str], None] = "aecabea0aca8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("noticias", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("data_evento", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("noticias", schema=None) as batch_op:
        batch_op.drop_column("data_evento")
