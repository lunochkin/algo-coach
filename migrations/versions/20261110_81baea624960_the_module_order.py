"""the module order

Revision: 81baea624960
Revises: adffd9977b13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "81baea624960"
down_revision: str | Sequence[str] | None = "adffd9977b13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "module_orders",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("module_ids", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("module_orders_client_named_check")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("module_orders_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("module_orders_pkey")),
        sa.UniqueConstraint("appended", name=op.f("module_orders_appended_key")),
        sa.UniqueConstraint(
            "user_id", "client_id", name=op.f("module_orders_user_id_client_id_key")
        ),
    )
    op.create_index(op.f("module_orders_user_id_idx"), "module_orders", ["user_id"], unique=False)

    # by hand, since Alembic generates no trigger: `README.md`, Storage
    op.execute(
        "CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON module_orders"
        " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
    )


def downgrade() -> None:
    op.drop_index(op.f("module_orders_user_id_idx"), table_name="module_orders")
    op.drop_table("module_orders")
