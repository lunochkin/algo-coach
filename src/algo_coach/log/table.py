from sqlalchemy import CheckConstraint, Column, Table, Text

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
