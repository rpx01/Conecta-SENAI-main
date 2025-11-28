"""create emails_secretaria table

Revision ID: 56583e4deb58
Revises: 96efaa1d27b2
Create Date: 2025-09-12 00:02:13.021829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56583e4deb58'
down_revision: Union[str, Sequence[str], None] = '96efaa1d27b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'emails_secretaria',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('emails_secretaria')
