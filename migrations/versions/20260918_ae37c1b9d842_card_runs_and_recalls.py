"""card runs and recall attempts

Revision: ae37c1b9d842
Revises: b41d7c5e9a20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "ae37c1b9d842"
down_revision: str | Sequence[str] | None = "b41d7c5e9a20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# named rather than declared, so a column referencing one creates none
HINT = postgresql.ENUM("title", "notes", "form", name="hint", create_type=False)
CASE_OUTCOME = postgresql.ENUM(
    "passed", "wrong", "timeout", "crashed", name="case_outcome", create_type=False
)

# the run and the recall are the user's log, and the rows each is stored with
APPEND_ONLY = (
    "card_runs",
    "card_run_probes",
    "recall_attempts",
    "recall_attempt_case_results",
)


def upgrade() -> None:
    # created once, before the table using it: a column declaring its own type
    # would create it a second time
    postgresql.ENUM("title", "notes", "form", name="hint").create(op.get_bind())

    op.create_table(
        "card_runs",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("card_id", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appended"),
    )
    op.create_index(op.f("card_runs_user_id_idx"), "card_runs", ["user_id"], unique=False)

    op.create_table(
        "card_run_probes",
        sa.Column("card_run_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Text(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["card_run_id"], ["card_runs.id"]),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.PrimaryKeyConstraint("card_run_id", "position"),
        sa.UniqueConstraint("card_run_id", "problem_id"),
    )

    op.create_table(
        "recall_attempts",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("card_id", sa.Text(), nullable=False),
        sa.Column("template_id", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("hints", postgresql.ARRAY(HINT), nullable=False),
        sa.Column("cap_ms", sa.Integer(), nullable=False),
        sa.Column("runner", sa.Text(), nullable=False),
        sa.CheckConstraint("cap_ms > 0", name="capped"),
        sa.CheckConstraint("runner <> ''", name="runner_named"),
        sa.ForeignKeyConstraint(["card_id"], ["cards.id"]),
        sa.ForeignKeyConstraint(["template_id"], ["card_templates.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("appended"),
    )
    op.create_index(
        op.f("recall_attempts_user_id_idx"), "recall_attempts", ["user_id"], unique=False
    )
    op.create_index(
        op.f("recall_attempts_template_id_idx"), "recall_attempts", ["template_id"], unique=False
    )

    op.create_table(
        "recall_attempt_case_results",
        sa.Column("recall_attempt_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Text(), nullable=False),
        sa.Column("outcome", CASE_OUTCOME, nullable=False),
        sa.Column("elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.CheckConstraint("elapsed_ms >= 0", name="elapsed_counted"),
        sa.CheckConstraint(
            "error IS NULL OR outcome = 'crashed'", name="only_a_crash_names_an_error"
        ),
        sa.CheckConstraint(
            "outcome NOT IN ('passed', 'wrong') OR elapsed_ms IS NOT NULL",
            name="returned_was_timed",
        ),
        sa.ForeignKeyConstraint(["recall_attempt_id"], ["recall_attempts.id"]),
        sa.PrimaryKeyConstraint("recall_attempt_id", "position"),
    )

    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON {table}"
            " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
        )


def downgrade() -> None:
    for table in APPEND_ONLY:
        op.execute(f"DROP TRIGGER append_only ON {table}")
    op.drop_table("recall_attempt_case_results")
    op.drop_index(op.f("recall_attempts_template_id_idx"), table_name="recall_attempts")
    op.drop_index(op.f("recall_attempts_user_id_idx"), table_name="recall_attempts")
    op.drop_table("recall_attempts")
    op.drop_table("card_run_probes")
    op.drop_index(op.f("card_runs_user_id_idx"), table_name="card_runs")
    op.drop_table("card_runs")
    postgresql.ENUM(name="hint").drop(op.get_bind())
