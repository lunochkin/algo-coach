"""a sitting's clock start

Revision: 0bd2109b024e
Revises: 4b1d7f0c2ae3
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0bd2109b024e"
down_revision: str | Sequence[str] | None = "4b1d7f0c2ae3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sittings", sa.Column("clock_started_at", sa.DateTime(timezone=True), nullable=True)
    )
    # every sitting so far started its clock as the statement was served
    op.execute("UPDATE sittings SET clock_started_at = started_at")
    op.create_check_constraint(
        op.f("sittings_clock_after_serving_check"),
        "sittings",
        "clock_started_at >= started_at",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("sittings_clock_after_serving_check"), "sittings", type_="check")
    op.drop_column("sittings", "clock_started_at")
