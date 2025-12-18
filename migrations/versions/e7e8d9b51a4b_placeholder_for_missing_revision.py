from typing import Sequence, Union


# Alembic revision identifiers
revision: str = "e7e8d9b51a4b"
down_revision: Union[str, Sequence[str], None] = "933546544697"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Placeholder to preserve migration history."""
    pass


def downgrade() -> None:
    pass
