"""Atualiza estrutura da tabela de notícias"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5b7b823a4e1a"
down_revision: Union[str, Sequence[str], None] = "b36d3e0a3a9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEXES = {
    "ix_noticias_ativo": ["ativo"],
    "ix_noticias_destaque": ["destaque"],
    "ix_noticias_data_publicacao": ["data_publicacao"],
    "ix_noticias_ativo_destaque_data": ["ativo", "destaque", "data_publicacao"],
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if "noticias" not in table_names:
        op.create_table(
            "noticias",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("titulo", sa.String(length=200), nullable=False),
            sa.Column("resumo", sa.String(length=500), nullable=True),
            sa.Column("conteudo", sa.Text(), nullable=False),
            sa.Column("autor", sa.String(length=120), nullable=True),
            sa.Column("imagem_url", sa.String(length=500), nullable=True),
            sa.Column("destaque", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("data_publicacao", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "criado_em",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "atualizado_em",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        for index_name, columns in INDEXES.items():
            op.create_index(index_name, "noticias", columns)
        return

    columns = {col["name"]: col for col in inspector.get_columns("noticias")}

    resumo_info = columns.get("resumo")
    if resumo_info:
        existing_type = sa.String(length=getattr(resumo_info["type"], "length", 400))
        op.alter_column(
            "noticias",
            "resumo",
            existing_type=existing_type,
            type_=sa.String(length=500),
            nullable=True,
            existing_nullable=resumo_info.get("nullable", True),
        )
    else:
        op.add_column("noticias", sa.Column("resumo", sa.String(length=500), nullable=True))

    data_publicacao_info = columns.get("data_publicacao")
    if data_publicacao_info:
        op.alter_column(
            "noticias",
            "data_publicacao",
            existing_type=sa.DateTime(),
            type_=sa.DateTime(timezone=True),
            nullable=True,
            existing_nullable=data_publicacao_info.get("nullable", True),
            server_default=None,
            existing_server_default=data_publicacao_info.get("default"),
        )
    else:
        op.add_column(
            "noticias",
            sa.Column("data_publicacao", sa.DateTime(timezone=True), nullable=True),
        )

    for column_name in ("criado_em", "atualizado_em"):
        column_info = columns.get(column_name)
        if column_info:
            op.alter_column(
                "noticias",
                column_name,
                existing_type=sa.DateTime(),
                type_=sa.DateTime(timezone=True),
                nullable=False,
                existing_nullable=column_info.get("nullable", False),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                existing_server_default=column_info.get("default"),
            )
        else:
            op.add_column(
                "noticias",
                sa.Column(
                    column_name,
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                ),
            )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("noticias")}
    for index_name, columns in INDEXES.items():
        if index_name not in existing_indexes:
            op.create_index(index_name, "noticias", columns)


def downgrade() -> None:
    existing_indexes = INDEXES.keys()
    for index_name in existing_indexes:
        op.drop_index(index_name, table_name="noticias")
    op.drop_table("noticias")
