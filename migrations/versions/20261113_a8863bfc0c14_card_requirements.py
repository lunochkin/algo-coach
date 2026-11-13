"""card_requirements

Revision: a8863bfc0c14
Revises: 10d25f6977e2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a8863bfc0c14"
down_revision: str | Sequence[str] | None = "10d25f6977e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "card_requirements",
        sa.Column("card_id", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("card", sa.Text(), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("used_by", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["card"], ["cards.slug"], name=op.f("card_requirements_card_fkey")),
        sa.ForeignKeyConstraint(
            ["card_id", "used_by"],
            ["card_templates.card_id", "card_templates.slug"],
            name="card_requirements_used_by_fkey",
        ),
        sa.ForeignKeyConstraint(
            ["card_id"], ["cards.id"], name=op.f("card_requirements_card_id_fkey")
        ),
        sa.PrimaryKeyConstraint("card_id", "position", name=op.f("card_requirements_pkey")),
        sa.UniqueConstraint(
            "card_id",
            "card",
            "template",
            "used_by",
            name=op.f("card_requirements_card_id_card_template_used_by_key"),
        ),
    )


def downgrade() -> None:
    op.drop_table("card_requirements")
