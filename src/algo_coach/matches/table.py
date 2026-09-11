from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Table, Text
from sqlalchemy.dialects.postgresql import ARRAY

from algo_coach.schema import MatchSource
from algo_coach.storage import call_column, enumerated, metadata, timestamp

template_matches = Table(
    "template_matches",
    metadata,
    Column("id", Text, primary_key=True),
    Column("created_at", timestamp(), nullable=False),
    Column("template_id", Text, ForeignKey("card_templates.id"), nullable=False),
    Column("solution_id", Text, ForeignKey("solutions.id"), nullable=False),
    Column("matched", Boolean, nullable=False),
    Column("source", enumerated(MatchSource), nullable=False),
    Column("informed_by", ARRAY(Text), nullable=False),
    call_column(nullable=True),
    # only the matcher names a call: the generator's match is an assertion, and
    # the user's is a reading, so neither carries provenance
    CheckConstraint("(source = 'classifier') = (call_id IS NOT NULL)", name="call_matches_source"),
)
