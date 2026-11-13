"""judgement_items

Revision: ce3e64c2034c
Revises: 8c4318844b03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "ce3e64c2034c"
down_revision: str | Sequence[str] | None = "8c4318844b03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# case_outcome exists already: named rather than declared, so none is created
CASE_OUTCOME = postgresql.ENUM(
    "passed", "wrong", "timeout", "crashed", name="case_outcome", create_type=False
)
ITEM_STATUS = postgresql.ENUM("served", "retired", name="item_status")


def upgrade() -> None:
    ITEM_STATUS.create(op.get_bind())
    op.create_table(
        "judgement_items",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("template_id", sa.Text(), nullable=False),
        sa.Column("form_digest", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("clean", sa.Boolean(), nullable=False),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.Column("change", sa.Text(), nullable=True),
        sa.Column(
            "case_args", postgresql.JSONB(none_as_null=True, astext_type=sa.Text()), nullable=True
        ),
        sa.Column("case_expected", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "outcome",
            CASE_OUTCOME,
            nullable=True,
        ),
        sa.Column("returned", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", postgresql.ENUM(name="item_status", create_type=False), nullable=False),
        sa.CheckConstraint(
            "form_digest <> '' AND code <> ''", name=op.f("judgement_items_built_check")
        ),
        sa.CheckConstraint(
            "outcome IS NULL OR outcome <> 'timeout'", name=op.f("judgement_items_no_timeout_check")
        ),
        sa.CheckConstraint(
            "clean = (line IS NULL AND change IS NULL AND case_args IS NULL AND outcome IS NULL)",
            name=op.f("judgement_items_a_flaw_names_its_line_check"),
        ),
        sa.ForeignKeyConstraint(
            ["template_id"], ["card_templates.id"], name=op.f("judgement_items_template_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("judgement_items_pkey")),
    )
    op.create_index(
        op.f("judgement_items_template_id_idx"), "judgement_items", ["template_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("judgement_items_template_id_idx"), table_name="judgement_items")
    op.drop_table("judgement_items")
    ITEM_STATUS.drop(op.get_bind())
