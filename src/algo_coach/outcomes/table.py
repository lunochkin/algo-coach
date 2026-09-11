from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY

from algo_coach.schema import CallSite, Gate
from algo_coach.storage import call_column, enumerated, metadata, timestamp

site_outcomes = Table(
    "site_outcomes",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("site", enumerated(CallSite), nullable=False),
    # no foreign key: a landing clears the draft the writing id names, and a
    # replay's writing never had a draft
    Column("writing_id", Text, nullable=False, index=True),
    Column("target_template_id", Text, ForeignKey("card_templates.id")),
    Column("target_technique", Text),
    Column("problem_id", Text, ForeignKey("problems.id")),
    Column("gate", enumerated(Gate)),
    Column("detail", Text, nullable=False),
    Column("mutants", Integer, nullable=False),
    Column("survived", Integer, nullable=False),
    Column("won", Integer, nullable=False),
    Column("killed", Integer, nullable=False),
    Column("rounds", ARRAY(Integer), nullable=False),
    Column("proposed", Integer, nullable=False),
    Column("misdeclared", Integer, nullable=False),
    Column("separating", Integer),
    Column("repeats", Integer, nullable=False),
    Column("unseparated", Text),
    Column("largest", Integer),
    # a site writes an outcome only where it made a call
    call_column(nullable=False),
    CheckConstraint("writing_id <> ''", name="writing_named"),
    CheckConstraint("target_template_id <> '' AND target_technique <> ''", name="target_named"),
    CheckConstraint("target_template_id IS NULL OR target_technique IS NULL", name="one_target"),
    CheckConstraint("repeats >= 1", name="called_at_least_once"),
    CheckConstraint("largest > 0", name="bound_positive"),
)
