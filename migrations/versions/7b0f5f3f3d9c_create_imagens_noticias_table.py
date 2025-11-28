"""create table to armazenar imagens de notícias"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "7b0f5f3f3d9c"
down_revision: Union[str, Sequence[str], None] = "5b7b823a4e1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("imagens_noticias"):
        op.create_table(
            "imagens_noticias",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "noticia_id",
                sa.Integer(),
                sa.ForeignKey("noticias.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("nome_arquivo", sa.String(length=255), nullable=False),
            sa.Column("caminho_relativo", sa.String(length=255), nullable=False),
            sa.Column(
                "criado_em",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
    else:
        colunas = {col["name"] for col in inspector.get_columns("imagens_noticias")}
        if "caminho_relativo" not in colunas:
            op.add_column(
                "imagens_noticias",
                sa.Column("caminho_relativo", sa.String(length=255), nullable=False, server_default=""),
            )
            op.execute(
                sa.text(
                    "UPDATE imagens_noticias SET caminho_relativo = nome_arquivo WHERE caminho_relativo = ''"
                )
            )
            op.alter_column(
                "imagens_noticias",
                "caminho_relativo",
                server_default=None,
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if inspector.has_table("imagens_noticias"):
        op.drop_table("imagens_noticias")
