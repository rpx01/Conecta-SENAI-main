from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9fd848c63563"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("turmas", schema=None) as batch_op:
        batch_op.alter_column(
            "nome",
            existing_type=sa.VARCHAR(length=50),
            type_=sa.String(length=255),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("turmas", schema=None) as batch_op:
        batch_op.alter_column(
            "nome",
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=50),
            existing_nullable=False,
        )
