from alembic import op
import sqlalchemy as sa


revision = "892341234567"
down_revision = "2f5d1f0614c3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("suporte_chamados", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("inicio_atendimento_at", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(sa.Column("encerrado_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("suporte_chamados", schema=None) as batch_op:
        batch_op.drop_column("encerrado_at")
        batch_op.drop_column("inicio_atendimento_at")
