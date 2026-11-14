"""judgements

Revision: a36fc93426bc
Revises: ce3e64c2034c
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a36fc93426bc"
down_revision: str | Sequence[str] | None = "ce3e64c2034c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "judgements",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("item_id", sa.Text(), nullable=False),
        sa.Column("called_clean", sa.Boolean(), nullable=False),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.CheckConstraint(
            "called_clean = (line IS NULL)", name=op.f("judgements_a_flaw_is_tapped_check")
        ),
        sa.ForeignKeyConstraint(
            ["item_id"], ["judgement_items.id"], name=op.f("judgements_item_id_fkey")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("judgements_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("judgements_pkey")),
        sa.UniqueConstraint("appended", name=op.f("judgements_appended_key")),
    )
    op.create_index(op.f("judgements_item_id_idx"), "judgements", ["item_id"], unique=False)
    op.create_index(op.f("judgements_user_id_idx"), "judgements", ["user_id"], unique=False)

    # by hand, since Alembic generates no trigger: `README.md`, Storage
    op.execute(
        "CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON judgements"
        " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
    )


def downgrade() -> None:
    op.drop_index(op.f("judgements_user_id_idx"), table_name="judgements")
    op.drop_index(op.f("judgements_item_id_idx"), table_name="judgements")
    op.drop_table("judgements")
