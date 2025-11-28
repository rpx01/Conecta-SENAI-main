"""add observacoes to suporte_chamados

Revision ID: 2f5d1f0614c3
Revises: d204e2f154dd
Create Date: 2025-02-14 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f5d1f0614c3"
down_revision: Union[str, Sequence[str], None] = "d204e2f154dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("suporte_chamados")}
    if "observacoes" not in columns:
        op.add_column("suporte_chamados", sa.Column("observacoes", sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("suporte_chamados")}
    if "observacoes" in columns:
        op.drop_column("suporte_chamados", "observacoes")

