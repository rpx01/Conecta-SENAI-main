"""merge heads after teoria_online addition

Revision ID: aecabea0aca8
Revises: 74ef32d8754e, aa0b6b279d7c, e417ea710acb
Create Date: 2025-09-11 00:00:00.000000

"""
from typing import Sequence, Union

revision: str = 'aecabea0aca8'
down_revision: Union[str, Sequence[str], None] = (
    '74ef32d8754e',
    'aa0b6b279d7c',
    'e417ea710acb',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
