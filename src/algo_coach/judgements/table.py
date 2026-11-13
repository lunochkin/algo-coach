from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, Table, Text
from sqlalchemy.dialects.postgresql import JSONB

from algo_coach.schema import CaseOutcome, ItemStatus
from algo_coach.storage import enumerated, metadata, timestamp

# created once, and only the status moves: `README.md`, Data classes
judgement_items = Table(
    "judgement_items",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("template_id", Text, ForeignKey("card_templates.id"), nullable=False, index=True),
    Column("form_digest", Text, nullable=False),
    Column("code", Text, nullable=False),
    Column("clean", Boolean, nullable=False),
    Column("line", Integer),
    Column("change", Text),
    # JSON of any shape by design, as a case's are. A `None` stores as JSON null
    Column("case_args", JSONB(none_as_null=True)),
    Column("case_expected", JSONB(none_as_null=False), nullable=False),
    Column("outcome", enumerated(CaseOutcome)),
    Column("returned", JSONB(none_as_null=False), nullable=False),
    Column("status", enumerated(ItemStatus), nullable=False),
    CheckConstraint("form_digest <> '' AND code <> ''", name="built"),
    CheckConstraint(
        "clean = (line IS NULL AND change IS NULL AND case_args IS NULL AND outcome IS NULL)",
        name="a_flaw_names_its_line",
    ),
    CheckConstraint("outcome IS NULL OR outcome <> 'timeout'", name="no_timeout"),
)
