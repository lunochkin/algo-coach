from sqlalchemy import Boolean, CheckConstraint, Column, Double, ForeignKey, Table, Text

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
