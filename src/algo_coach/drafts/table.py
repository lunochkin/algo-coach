from enum import StrEnum

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

from algo_coach.schema import ExpectedSource, Gate, ProblemDifficulty, WritingState
from algo_coach.storage import call_column, enumerated, metadata

# which of a draft's lists of settled cases a row belongs to, named as the
# draft's field is
SettledField = StrEnum(
    "SettledField", {name.upper(): name for name in ("cases", "kept", "won", "separating_case")}
)


def _owned_by_the_draft() -> Column[str]:
    # a landing clears the draft, and what it held goes with it
    return Column("draft_id", Text, ForeignKey("drafts.id", ondelete="CASCADE"), primary_key=True)


drafts = Table(
    "drafts",
    metadata,
    Column("id", Text, primary_key=True),
    Column("state", enumerated(WritingState), nullable=False),
    Column("gate", enumerated(Gate)),
    Column("problem_id", Text, ForeignKey("problems.id")),
    Column("target_template_id", Text, ForeignKey("card_templates.id")),
    Column("target_technique", Text),
    Column("title", Text, nullable=False),
    Column("statement", Text, nullable=False),
    Column("canonical", Text, nullable=False),
    Column("difficulty", enumerated(ProblemDifficulty), nullable=False),
    Column("reference", Text),
    Column("input_generator", Text),
    Column("largest", Integer),
    Column("naive", Text),
    Column("unseparated", Text),
    Column("ceiling", Integer),
    Column("margin", Integer),
    Column("repeats_max", Integer),
    Column("search_revision", Integer),
    # the call each site made, which holds the configuration and the prompt
    # hash a resume compares with what it would send now
    Column("generator_call_id", Text, ForeignKey("calls.id")),
    Column("blind_call_id", Text, ForeignKey("calls.id")),
    Column("inputs_call_id", Text, ForeignKey("calls.id")),
    Column("naive_call_id", Text, ForeignKey("calls.id")),
    Column("discrimination_call_id", Text, ForeignKey("calls.id")),
    CheckConstraint(
        "id <> '' AND title <> '' AND statement <> '' AND canonical <> ''", name="drafted_written"
    ),
    CheckConstraint(
        "reference <> '' AND input_generator <> '' AND naive <> '' AND unseparated <> ''",
        name="later_steps_written",
    ),
    CheckConstraint("(state = 'rejected') = (gate IS NOT NULL)", name="rejection_names_its_gate"),
    CheckConstraint(
        "(state = 'landed') = (problem_id IS NOT NULL)", name="landing_names_the_problem"
    ),
    CheckConstraint("target_template_id <> '' AND target_technique <> ''", name="target_named"),
    CheckConstraint("target_template_id IS NULL OR target_technique IS NULL", name="one_target"),
    CheckConstraint(
        "(input_generator IS NULL) = (largest IS NULL)", name="input_generator_carries_its_bound"
    ),
    CheckConstraint(
        "largest > 0 AND ceiling > 0 AND margin > 0 AND repeats_max > 0 AND search_revision > 0",
        name="bounds_positive",
    ),
)

# the cases the generator's own call declared, in its order
draft_declared_cases = Table(
    "draft_declared_cases",
    metadata,
    _owned_by_the_draft(),
    Column("position", Integer, primary_key=True),
    Column("args", JSONB(none_as_null=False), nullable=False),
    Column("expected", JSONB(none_as_null=False), nullable=False),
    CheckConstraint("jsonb_typeof(args) = 'array'", name="args_positional"),
)

# the cases a run settled, in each of the draft's lists; the separating case
# is a list of one
draft_settled_cases = Table(
    "draft_settled_cases",
    metadata,
    _owned_by_the_draft(),
    Column("draft_field", enumerated(SettledField), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("args", JSONB(none_as_null=False), nullable=False),
    Column("expected", JSONB(none_as_null=False), nullable=False),
    Column("expected_from", enumerated(ExpectedSource), nullable=False),
    Column("round", Integer),
    Column("repeats", Integer, nullable=False),
    # the call that proposed the arguments, which holds its configuration
    call_column(nullable=False),
    CheckConstraint("jsonb_typeof(args) = 'array'", name="args_positional"),
    CheckConstraint("round >= 0", name="round_counted"),
    CheckConstraint("repeats >= 1", name="called_at_least_once"),
    CheckConstraint("draft_field <> 'separating_case' OR position = 0", name="one_separating_case"),
)
