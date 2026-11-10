"""a question's level, not its rank

Revision: 105544fa7f80
Revises: f326fd1871e5
"""

from collections.abc import Sequence

from alembic import op

revision: str = "105544fa7f80"
down_revision: str | Sequence[str] | None = "f326fd1871e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# by hand: autogenerate reads a renamed column as one dropped and one added
COLUMNS = [
    ("questions", "rank", "level"),
    ("stints", "rank", "level"),
    ("certification_exams", "rank", "level"),
    ("focuses", "certification_rank", "certification_level"),
]
CHECKS = [
    ("questions", "rank_ranked", "level_in_range"),
    ("stints", "rank_ranked", "level_in_range"),
    ("stints", "an_exam_names_its_rank", "an_exam_names_its_level"),
    ("certification_exams", "rank_ranked", "level_in_range"),
    ("focuses", "rank_ranked", "level_in_range"),
]
# Postgres 18 names a column's NOT NULL after the column, and a rename keeps it
NOT_NULLS = [
    ("questions", "rank_not_null", "level_not_null"),
    ("certification_exams", "rank_not_null", "level_not_null"),
]


Renames = list[tuple[str, str, str]]


def _rename(columns: Renames, constraints: Renames) -> None:
    for table, old, new in columns:
        op.alter_column(table, old, new_column_name=new)
    for table, old, new in constraints:
        op.execute(f"ALTER TABLE {table} RENAME CONSTRAINT {table}_{old} TO {table}_{new}")


def _checks(checks: Renames) -> Renames:
    return [(t, f"{old}_check", f"{new}_check") for t, old, new in checks]


def upgrade() -> None:
    _rename(COLUMNS, _checks(CHECKS) + NOT_NULLS)


def downgrade() -> None:
    _rename(
        [(t, new, old) for t, old, new in COLUMNS],
        [(t, new, old) for t, old, new in _checks(CHECKS) + NOT_NULLS],
    )
