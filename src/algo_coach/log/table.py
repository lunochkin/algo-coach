from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Double,
    ForeignKey,
    Index,
    Integer,
    Table,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY

from algo_coach.schema import CaseOutcome, ClaimSource, Confidence, FailureMode
from algo_coach.storage import call_column, enumerated, metadata, timestamp

# the engine's own user, whose id a private record's `user_id` references. The
# account a person signs in with is linked to it, and never stands in for it
users = Table(
    "users",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    CheckConstraint("id <> ''", name="id_minted"),
)

attempts = Table(
    "attempts",
    metadata,
    Column("id", Text, primary_key=True),
    # the board and the candidates read one user's attempts
    Column("user_id", Text, ForeignKey("users.id"), nullable=False, index=True),
    Column("problem_id", Text, ForeignKey("problems.id"), nullable=False),
    # the claim prompt reads one sitting's attempts
    Column("sitting_id", Text, ForeignKey("sittings.id"), index=True),
    Column("started_at", timestamp()),
    Column("finished_at", timestamp(), nullable=False),
    Column("language", Text),
    Column("time_to_solve_sec", Double[float]()),
    Column("solved", Boolean, nullable=False),
    Column("code", Text),
    CheckConstraint("time_to_solve_sec >= 0", name="time_counted"),
)

sittings = Table(
    "sittings",
    metadata,
    Column("id", Text, primary_key=True),
    Column("user_id", Text, ForeignKey("users.id"), nullable=False),
    Column("problem_id", Text, ForeignKey("problems.id"), nullable=False),
    Column("started_at", timestamp(), nullable=False),
    Column("ended_at", timestamp()),
    CheckConstraint("ended_at >= started_at", name="ends_after_it_starts"),
    # one clock running on a problem for a user: a second serve reaches it
    # rather than starting another
    Index(
        "sittings_one_running_idx",
        "user_id",
        "problem_id",
        unique=True,
        postgresql_where=text("ended_at IS NULL"),
    ),
)

# a sitting's pauses, in order. That they follow the start and each other, and
# that only the last is open, spans rows, and stays the record's own check
sitting_pauses = Table(
    "sitting_pauses",
    metadata,
    Column("sitting_id", Text, ForeignKey("sittings.id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("at", timestamp(), nullable=False),
    Column("until", timestamp()),
    CheckConstraint("until >= at", name="ends_no_earlier_than_it_starts"),
)

attempt_verifications = Table(
    "attempt_verifications",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("attempt_id", Text, ForeignKey("attempts.id"), nullable=False, index=True),
    Column("cap_ms", Integer, nullable=False),
    Column("runner", Text, nullable=False),
    CheckConstraint("cap_ms > 0", name="capped"),
    CheckConstraint("runner <> ''", name="runner_named"),
)

# the same shape as a solution run's results, declared here rather than
# imported: the private log reads no product store's module
attempt_verification_case_results = Table(
    "attempt_verification_case_results",
    metadata,
    Column(
        "attempt_verification_id", Text, ForeignKey("attempt_verifications.id"), primary_key=True
    ),
    Column("position", Integer, primary_key=True),
    Column("case_id", Text, ForeignKey("test_cases.id"), nullable=False),
    Column("outcome", enumerated(CaseOutcome), nullable=False),
    Column("elapsed_ms", Integer),
    Column("error", Text),
    CheckConstraint(
        "outcome NOT IN ('passed', 'wrong') OR elapsed_ms IS NOT NULL", name="returned_was_timed"
    ),
    CheckConstraint("error IS NULL OR outcome = 'crashed'", name="only_a_crash_names_an_error"),
    CheckConstraint("elapsed_ms >= 0", name="elapsed_counted"),
)

attempt_claims = Table(
    "attempt_claims",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("attempt_id", Text, ForeignKey("attempts.id"), nullable=False, index=True),
    Column("techniques", ARRAY(Text), nullable=False),
    Column("declined", Boolean, nullable=False),
    Column("source", enumerated(ClaimSource), nullable=False),
    Column("informed_by", ARRAY(Text), nullable=False),
    Column("confidence", enumerated(Confidence)),
    call_column(nullable=True),
    # the claim's own rules: a user names a technique or declines, a decline
    # names nothing, and only the classifier names a call
    CheckConstraint(
        "source <> 'user' OR cardinality(techniques) > 0 OR declined", name="user_claim_answers"
    ),
    CheckConstraint("NOT (cardinality(techniques) > 0 AND declined)", name="decline_names_nothing"),
    CheckConstraint("(source = 'classifier') = (call_id IS NOT NULL)", name="call_matches_source"),
)

self_labels = Table(
    "self_labels",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("attempt_id", Text, ForeignKey("attempts.id"), nullable=False, index=True),
    Column("mode", enumerated(FailureMode), nullable=False),
)

diagnoses = Table(
    "diagnoses",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("attempt_id", Text, ForeignKey("attempts.id"), nullable=False, index=True),
    Column("mode", enumerated(FailureMode), nullable=False),
    Column("evidence", Text, nullable=False),
    # a model wrote every diagnosis
    call_column(nullable=False),
)
