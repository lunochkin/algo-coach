"""two hints

Revision: 4b1d7f0c2ae3
Revises: ae37c1b9d842
"""

from collections.abc import Sequence

from alembic import op

revision: str = "4b1d7f0c2ae3"
down_revision: str | Sequence[str] | None = "ae37c1b9d842"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # the trainer names the template now, so the title answers nothing a hint
    # was for. Postgres drops no enum value, so the type is written again
    op.execute("SET LOCAL algo_coach.erasing = 'on'")
    # the case results first: they key to the attempt they were run under
    op.execute(
        "DELETE FROM recall_attempt_case_results WHERE recall_attempt_id IN"
        " (SELECT id FROM recall_attempts WHERE 'title' = ANY(hints))"
    )
    op.execute("DELETE FROM recall_attempts WHERE 'title' = ANY(hints)")
    op.execute("ALTER TYPE hint RENAME TO hint_old")
    op.execute("CREATE TYPE hint AS ENUM ('notes', 'form')")
    op.execute(
        "ALTER TABLE recall_attempts ALTER COLUMN hints TYPE hint[] USING hints::text[]::hint[]"
    )
    op.execute("DROP TYPE hint_old")


def downgrade() -> None:
    op.execute("ALTER TYPE hint RENAME TO hint_old")
    op.execute("CREATE TYPE hint AS ENUM ('title', 'notes', 'form')")
    op.execute(
        "ALTER TABLE recall_attempts ALTER COLUMN hints TYPE hint[] USING hints::text[]::hint[]"
    )
    op.execute("DROP TYPE hint_old")
