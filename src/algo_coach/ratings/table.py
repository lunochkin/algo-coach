from sqlalchemy import CheckConstraint, Column, ForeignKey, Table, Text

from algo_coach.schema import ClaimSource, ProblemDifficulty
from algo_coach.storage import appended_column, call_column, enumerated, metadata, timestamp

difficulty_ratings = Table(
    "difficulty_ratings",
    metadata,
    Column("id", Text, primary_key=True),
    appended_column(),
    Column("created_at", timestamp(), nullable=False),
    Column("problem_id", Text, ForeignKey("problems.id"), nullable=False, index=True),
    Column("difficulty", enumerated(ProblemDifficulty), nullable=False),
    Column("source", enumerated(ClaimSource), nullable=False),
    call_column(nullable=True),
    CheckConstraint("(source = 'classifier') = (call_id IS NOT NULL)", name="call_matches_source"),
)
