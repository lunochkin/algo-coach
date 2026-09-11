from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

from algo_coach.schema import ExpectedSource
from algo_coach.storage import appended_column, call_column, enumerated, metadata

test_cases = Table(
    "test_cases",
    metadata,
    Column("id", Text, primary_key=True),
    appended_column(),
    # a run reads a problem's whole set
    Column("problem_id", Text, ForeignKey("problems.id"), nullable=False, index=True),
    # JSON of any shape by design, so JSONB. A `None` the solution returns is
    # stored as JSON `null`, a value, so the column stays NOT NULL
    Column("args", JSONB(none_as_null=False), nullable=False),
    Column("expected", JSONB(none_as_null=False), nullable=False),
    Column("expected_from", enumerated(ExpectedSource), nullable=False),
    # absent on the separating case, which no round won
    Column("round", Integer),
    Column("repeats", Integer, nullable=False),
    # a model proposed every case's arguments
    call_column(nullable=False),
    CheckConstraint("jsonb_typeof(args) = 'array'", name="args_positional"),
    CheckConstraint("round >= 0", name="round_counted"),
    CheckConstraint("repeats >= 1", name="called_at_least_once"),
)
