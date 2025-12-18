from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8055be39141c"
down_revision: Union[str, Sequence[str], None] = "56583e4deb58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("secretaria_treinamentos"):
        op.create_table(
            "secretaria_treinamentos",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("nome", sa.String(length=255), nullable=False),
            sa.Column(
                "email",
                sa.String(length=255),
                nullable=False,
                unique=True,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("secretaria_treinamentos"):
        op.drop_table("secretaria_treinamentos")
