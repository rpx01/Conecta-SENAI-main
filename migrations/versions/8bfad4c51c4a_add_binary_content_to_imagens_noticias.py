"""Add binary content columns to imagens_noticias.

Revision ID: 8bfad4c51c4a
Revises: 7b0f5f3f3d9c
Create Date: 2024-06-09
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision: str = "8bfad4c51c4a"
down_revision: Union[str, Sequence[str], None] = "7b0f5f3f3d9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("imagens_noticias"):
        return

    colunas = {col["name"] for col in inspector.get_columns("imagens_noticias")}

    if "conteudo" not in colunas:
        op.add_column(
            "imagens_noticias",
            sa.Column("conteudo", sa.LargeBinary(), nullable=True),
        )

    if "content_type" not in colunas:
        op.add_column(
            "imagens_noticias",
            sa.Column(
                "content_type",
                sa.String(length=255),
                nullable=False,
                server_default="application/octet-stream",
            ),
        )
        op.execute(
            text(
                "UPDATE imagens_noticias SET content_type = 'application/octet-stream' WHERE content_type IS NULL"
            )
        )
        op.alter_column(
            "imagens_noticias",
            "content_type",
            existing_type=sa.String(length=255),
            nullable=False,
            server_default=None,
        )

    if "tem_conteudo" not in colunas:
        op.add_column(
            "imagens_noticias",
            sa.Column(
                "tem_conteudo",
                sa.Boolean(),
                nullable=False,
                server_default=text("false"),
            ),
        )
        op.execute(
            text(
                "UPDATE imagens_noticias SET tem_conteudo = 1 WHERE conteudo IS NOT NULL"
            )
        )
        op.alter_column(
            "imagens_noticias",
            "tem_conteudo",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=None,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("imagens_noticias"):
        return

    colunas = {col["name"] for col in inspector.get_columns("imagens_noticias")}

    if "content_type" in colunas:
        op.drop_column("imagens_noticias", "content_type")

    if "tem_conteudo" in colunas:
        op.drop_column("imagens_noticias", "tem_conteudo")

    if "conteudo" in colunas:
        op.drop_column("imagens_noticias", "conteudo")
