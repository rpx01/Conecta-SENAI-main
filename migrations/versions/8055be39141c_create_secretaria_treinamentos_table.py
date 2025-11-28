"""create secretaria_treinamentos table

Revision ID: 8055be39141c
Revises: 56583e4deb58
Create Date: 2025-09-12 01:09:12.995095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8055be39141c'
down_revision: Union[str, Sequence[str], None] = '56583e4deb58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create secretaria_treinamentos table."""
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
    """Drop secretaria_treinamentos table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("secretaria_treinamentos"):
        op.drop_table("secretaria_treinamentos")
