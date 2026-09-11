from sqlalchemy import CheckConstraint, Column, ForeignKey, Table, Text

from algo_coach.schema import ProblemDifficulty, ProblemStatus, RetirementReason
from algo_coach.storage import call_column, enumerated, metadata

# `techniques` has no column: it is derived from the solution claims, and the
# problem store refuses a record carrying it
problems = Table(
    "problems",
    metadata,
    Column("id", Text, primary_key=True),
    Column("title", Text, nullable=False),
    Column("difficulty", enumerated(ProblemDifficulty)),
    Column("statement", Text, nullable=False),
    Column("target_template_id", Text, ForeignKey("card_templates.id")),
    Column("target_technique", Text),
    Column("status", enumerated(ProblemStatus), nullable=False),
    Column("retired_reason", enumerated(RetirementReason)),
    # the engine wrote every problem, so every one names its call
    call_column(nullable=False),
    CheckConstraint("statement <> ''", name="statement_written"),
    CheckConstraint("target_template_id <> '' AND target_technique <> ''", name="target_named"),
    CheckConstraint("target_template_id IS NULL OR target_technique IS NULL", name="one_target"),
    CheckConstraint(
        "(status = 'retired') = (retired_reason IS NOT NULL)", name="retirement_names_its_reason"
    ),
)
