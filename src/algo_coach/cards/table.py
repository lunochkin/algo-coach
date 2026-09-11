from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY

from algo_coach.schema import ProblemDifficulty, TemplateKind
from algo_coach.storage import enumerated, metadata

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
