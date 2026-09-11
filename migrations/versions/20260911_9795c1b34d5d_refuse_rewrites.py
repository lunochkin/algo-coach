"""refuse rewrites

Revision: 9795c1b34d5d
Revises: 24d3fa6eee53
"""

from collections.abc import Sequence

from alembic import op

revision: str = "9795c1b34d5d"
down_revision: str | Sequence[str] | None = "24d3fa6eee53"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# the append-only records, `README.md`'s invariants, and the case results a run
# is stored with. Written out: a migration keeps the list it was applied with
APPEND_ONLY = (
    "calls",
    "test_cases",
    "solutions",
    "solution_claims",
    "template_matches",
    "verifications",
    "verification_case_results",
    "site_outcomes",
    "attempts",
    "attempt_verifications",
    "attempt_verification_case_results",
    "attempt_claims",
    "self_labels",
    "diagnoses",
)


def upgrade() -> None:
    # per statement, so an update matching no row is refused too. TRUNCATE
    # fires no such trigger, which leaves the test fixture its reset
    op.execute(
        """
        CREATE FUNCTION refuse_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only: % refused', TG_TABLE_NAME, TG_OP;
        END
        $$
        """
    )
    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON {table}"
            " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
        )


def downgrade() -> None:
    for table in APPEND_ONLY:
        op.execute(f"DROP TRIGGER append_only ON {table}")
    op.execute("DROP FUNCTION refuse_rewrite()")
