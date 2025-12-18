from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "18fee14ce212"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.add_column(sa.Column("cpf", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("data_nascimento", sa.Date(), nullable=True))
        batch_op.add_column(sa.Column("empresa", sa.String(length=150), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("usuarios", schema=None) as batch_op:
        batch_op.drop_column("empresa")
        batch_op.drop_column("data_nascimento")
        batch_op.drop_column("cpf")
