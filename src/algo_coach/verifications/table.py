from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Table, Text

from algo_coach.schema import CaseOutcome
from algo_coach.storage import enumerated, metadata, timestamp

verifications = Table(
    "verifications",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("solution_id", Text, ForeignKey("solutions.id"), nullable=False, index=True),
    Column("cap_ms", Integer, nullable=False),
    Column("runner", Text, nullable=False),
    CheckConstraint("cap_ms > 0", name="capped"),
    CheckConstraint("runner <> ''", name="runner_named"),
)

# one row per case the run covered, in the order the run took them
verification_case_results = Table(
    "verification_case_results",
    metadata,
    Column("verification_id", Text, ForeignKey("verifications.id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("case_id", Text, ForeignKey("test_cases.id"), nullable=False),
    Column("outcome", enumerated(CaseOutcome), nullable=False),
    Column("elapsed_ms", Integer),
    Column("error", Text),
    # the result's own rules: a value the child returned was timed, and only a
    # crash names what raised
    CheckConstraint(
        "outcome NOT IN ('passed', 'wrong') OR elapsed_ms IS NOT NULL", name="returned_was_timed"
    ),
    CheckConstraint("error IS NULL OR outcome = 'crashed'", name="only_a_crash_names_an_error"),
    CheckConstraint("elapsed_ms >= 0", name="elapsed_counted"),
)
