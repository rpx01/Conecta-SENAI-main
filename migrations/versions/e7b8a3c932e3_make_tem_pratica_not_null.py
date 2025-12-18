from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b8a3c932e3"
down_revision: Union[str, Sequence[str], None] = "1c02b7a6da56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("treinamentos")]
    if "tem_pratica" not in columns:
        op.add_column(
            "treinamentos",
            sa.Column(
                "tem_pratica",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    else:
        op.alter_column(
            "treinamentos",
            "tem_pratica",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )
    op.execute("UPDATE treinamentos SET tem_pratica = FALSE WHERE tem_pratica IS NULL")
    op.alter_column("treinamentos", "tem_pratica", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns("treinamentos")]
    if "tem_pratica" in columns:
        op.alter_column(
            "treinamentos",
            "tem_pratica",
            existing_type=sa.Boolean(),
            nullable=True,
        )
