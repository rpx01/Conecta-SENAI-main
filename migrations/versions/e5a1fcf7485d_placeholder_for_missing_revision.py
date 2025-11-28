"""Placeholder revision to satisfy alembic graph"""

from typing import Sequence, Union

revision: str = 'e5a1fcf7485d'
down_revision: Union[str, Sequence[str], None] = 'e417ea710acb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
