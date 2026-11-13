"""difficulty_ratings

Revision: add978a5c77a
Revises: 9843bfb92965
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "add978a5c77a"
down_revision: str | Sequence[str] | None = "9843bfb92965"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# both types exist already: named rather than declared, so none is created
PROBLEM_DIFFICULTY = postgresql.ENUM(
    "easy", "medium", "hard", name="problem_difficulty", create_type=False
)
CLAIM_SOURCE = postgresql.ENUM("user", "classifier", name="claim_source", create_type=False)


def upgrade() -> None:
    op.create_table(
        "difficulty_ratings",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("problem_id", sa.Text(), nullable=False),
        sa.Column("difficulty", PROBLEM_DIFFICULTY, nullable=False),
        sa.Column("source", CLAIM_SOURCE, nullable=False),
        sa.Column("call_id", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "(source = 'classifier') = (call_id IS NOT NULL)",
            name=op.f("difficulty_ratings_call_matches_source_check"),
        ),
        sa.ForeignKeyConstraint(
            ["call_id"], ["calls.id"], name=op.f("difficulty_ratings_call_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"], ["problems.id"], name=op.f("difficulty_ratings_problem_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("difficulty_ratings_pkey")),
        sa.UniqueConstraint("appended", name=op.f("difficulty_ratings_appended_key")),
    )
    op.create_index(
        op.f("difficulty_ratings_problem_id_idx"),
        "difficulty_ratings",
        ["problem_id"],
        unique=False,
    )
    # by hand, since Alembic generates no trigger: `README.md`, Storage
    op.execute(
        "CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON difficulty_ratings"
        " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
    )


def downgrade() -> None:
    op.drop_index(op.f("difficulty_ratings_problem_id_idx"), table_name="difficulty_ratings")
    op.drop_table("difficulty_ratings")
