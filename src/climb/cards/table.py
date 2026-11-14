from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from climb.schema import ProblemDifficulty, TemplateKind
from climb.storage import enumerated, metadata

# a slug as `Slug` spells it
SLUG = "'^[a-z0-9][a-z0-9-]*$'"

cards = Table(
    "cards",
    metadata,
    Column("id", Text, primary_key=True),
    # a re-seed finds the card by its slug
    Column("slug", Text, nullable=False, unique=True),
    Column("technique", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("trigger", Text, nullable=False),
    Column("brief", Text, nullable=False),
    Column("selector_technique", Text, nullable=False),
    Column("selector_difficulty", ARRAY(enumerated(ProblemDifficulty)), nullable=False),
    Column("selector_size", Integer, nullable=False),
    CheckConstraint(f"slug ~ {SLUG}", name="slug_spelled"),
    CheckConstraint("trigger <> '' AND brief <> ''", name="trigger_and_brief_written"),
    CheckConstraint("selector_size >= 1", name="ladder_of_something"),
)

card_templates = Table(
    "card_templates",
    metadata,
    Column("id", Text, primary_key=True),
    Column("card_id", Text, ForeignKey("cards.id"), nullable=False),
    Column("position", Integer, nullable=False),
    Column("slug", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("trigger", Text, nullable=False),
    Column("notes", Text),
    Column("optional", Boolean, nullable=False),
    Column("speedup", Boolean, nullable=False),
    Column("kind", enumerated(TemplateKind), nullable=False),
    Column("code", Text, nullable=False),
    Column("unordered", Boolean, nullable=False, server_default=text("false")),
    Column("harness", ARRAY(Text), nullable=False, server_default=text("'{}'")),
    UniqueConstraint("card_id", "position"),
    # a re-seed matches a template by its slug within the card
    UniqueConstraint("card_id", "slug"),
    CheckConstraint(f"slug ~ {SLUG}", name="slug_spelled"),
    CheckConstraint("trigger <> ''", name="trigger_written"),
    # at most one optional template to a card; that a card is not all optional
    # spans rows, and stays the record's own check
    Index(
        "card_templates_one_optional_idx", "card_id", unique=True, postgresql_where=text("optional")
    ),
)


# one row per case a template's form is checked against, in the authored order
template_cases = Table(
    "template_cases",
    metadata,
    Column("template_id", Text, ForeignKey("card_templates.id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    # JSON of any shape by design, so JSONB. A `None` the form returns is stored
    # as JSON `null`, a value, so the column stays NOT NULL
    Column("args", JSONB(none_as_null=False), nullable=False),
    Column("expected", JSONB(none_as_null=False), nullable=False),
    CheckConstraint("jsonb_typeof(args) = 'array'", name="args_positional"),
)


# the card graph's edges, each on the requiring card: `content.md`. Slugs, as
# the record names them. That the required template exists and is core spans
# two cards, and stays the seed's check
card_requirements = Table(
    "card_requirements",
    metadata,
    Column("card_id", Text, ForeignKey("cards.id"), primary_key=True),
    Column("position", Integer, primary_key=True),
    Column("card", Text, ForeignKey("cards.slug"), nullable=False),  # the required card
    Column("template", Text, nullable=False),
    Column("used_by", Text, nullable=False),
    ForeignKeyConstraint(
        ["card_id", "used_by"],
        ["card_templates.card_id", "card_templates.slug"],
        name="card_requirements_used_by_fkey",
    ),
    UniqueConstraint("card_id", "card", "template", "used_by"),
)
