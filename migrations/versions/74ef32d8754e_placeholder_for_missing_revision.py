"""Placeholder revision for missing merge dependency"""

from typing import Sequence, Union

revision: str = '74ef32d8754e'
down_revision: Union[str, Sequence[str], None] = 'e417ea710acb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
