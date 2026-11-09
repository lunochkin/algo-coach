"""a template's cases

Revision: c3f81a06de47
Revises: 9bb6abb1a049
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3f81a06de47"
down_revision: str | Sequence[str] | None = "9bb6abb1a049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "template_cases",
        sa.Column("template_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("args", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expected", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("jsonb_typeof(args) = 'array'", name="args_positional"),
        sa.ForeignKeyConstraint(["template_id"], ["card_templates.id"]),
        sa.PrimaryKeyConstraint("template_id", "position"),
    )


def downgrade() -> None:
    op.drop_table("template_cases")
