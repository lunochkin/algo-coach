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

from algo_coach.storage import metadata, timestamp

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
