from sqlalchemy import CheckConstraint, Column, ForeignKey, Table, Text

from algo_coach.schema import SolutionRole
from algo_coach.storage import call_column, enumerated, metadata, timestamp

solutions = Table(
    "solutions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("problem_id", Text, ForeignKey("problems.id"), nullable=False),
    Column("role", enumerated(SolutionRole), nullable=False),
    Column("code", Text, nullable=False),
    # a model wrote every solution, so every one names its call
    call_column(nullable=False),
    CheckConstraint("code <> ''", name="code_written"),
)
