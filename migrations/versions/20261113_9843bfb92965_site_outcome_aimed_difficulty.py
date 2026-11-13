"""site_outcome_aimed_difficulty

Revision: 9843bfb92965
Revises: ca504c1a0182
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9843bfb92965"
down_revision: str | Sequence[str] | None = "ca504c1a0182"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# the type exists since the first migration; named rather than declared, so the
# column creates none
PROBLEM_DIFFICULTY = postgresql.ENUM(
    "easy", "medium", "hard", name="problem_difficulty", create_type=False
)


def upgrade() -> None:
    op.add_column("site_outcomes", sa.Column("aimed_difficulty", PROBLEM_DIFFICULTY, nullable=True))
    op.create_check_constraint(
        op.f("site_outcomes_aim_on_generator_check"),
        "site_outcomes",
        "aimed_difficulty IS NULL OR site = 'generator'",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("site_outcomes_aim_on_generator_check"), "site_outcomes", type_="check")
    op.drop_column("site_outcomes", "aimed_difficulty")
