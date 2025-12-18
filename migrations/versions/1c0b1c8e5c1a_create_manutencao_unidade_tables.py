from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "1c0b1c8e5c1a"
down_revision: Union[str, None] = "aecabea0aca8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "manutencao_areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False, unique=True),
    )
    op.create_table(
        "manutencao_tipos_servico",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=120), nullable=False, unique=True),
    )
    op.create_table(
        "manutencao_chamados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("nome_solicitante", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=False),
        sa.Column("area", sa.String(length=120), nullable=False),
        sa.Column(
            "tipo_servico_id",
            sa.Integer(),
            sa.ForeignKey("manutencao_tipos_servico.id"),
            nullable=False,
        ),
        sa.Column("patrimonio", sa.String(length=120), nullable=True),
        sa.Column("numero_serie", sa.String(length=120), nullable=True),
        sa.Column("descricao_problema", sa.Text(), nullable=False),
        sa.Column(
            "nivel_urgencia",
            sa.String(length=20),
            nullable=False,
            server_default="Baixo",
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="Aberto"
        ),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("local_unidade", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("inicio_atendimento_at", sa.DateTime(), nullable=True),
        sa.Column("encerrado_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "manutencao_anexos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "chamado_id",
            sa.Integer(),
            sa.ForeignKey("manutencao_chamados.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(length=255), nullable=False),
    )
    op.create_index(
        "ix_manutencao_chamados_tipo_servico",
        "manutencao_chamados",
        ["tipo_servico_id"],
    )
    op.create_index(
        "ix_manutencao_chamados_status",
        "manutencao_chamados",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_manutencao_chamados_status", table_name="manutencao_chamados")
    op.drop_index(
        "ix_manutencao_chamados_tipo_servico", table_name="manutencao_chamados"
    )
    op.drop_table("manutencao_anexos")
    op.drop_table("manutencao_chamados")
    op.drop_table("manutencao_tipos_servico")
    op.drop_table("manutencao_areas")
