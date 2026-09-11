from sqlalchemy import CheckConstraint, Column, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY

from algo_coach.schema import ClaimSource
from algo_coach.storage import call_column, enumerated, metadata, timestamp

solution_claims = Table(
    "solution_claims",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("solution_id", Text, ForeignKey("solutions.id"), nullable=False),
    Column("techniques", ARRAY(Text), nullable=False),
    Column("source", enumerated(ClaimSource), nullable=False),
    Column("informed_by", ARRAY(Text), nullable=False),
    call_column(nullable=True),
    # the classifier names its call and the user names none, as the record's
    # own validator requires
    CheckConstraint("(source = 'classifier') = (call_id IS NOT NULL)", name="call_matches_source"),
)
