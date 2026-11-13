"""a_copied_retirement

Revision: 10d25f6977e2
Revises: f59f7d65cc9f
"""

from collections.abc import Sequence

from alembic import op

revision: str = "10d25f6977e2"
down_revision: str | Sequence[str] | None = "f59f7d65cc9f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE retirement_reason ADD VALUE 'copied' AFTER 'defective'")


def downgrade() -> None:
    # Postgres drops no enum value, so the one added above stays
    pass
