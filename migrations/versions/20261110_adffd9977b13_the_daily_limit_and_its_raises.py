"""the daily limit and its raises

Revision: adffd9977b13
Revises: 105544fa7f80
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "adffd9977b13"
down_revision: str | Sequence[str] | None = "105544fa7f80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPEND_ONLY = ("daily_limits", "limit_raises")


def upgrade() -> None:
    op.create_table(
        "daily_limits",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("new_per_day", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("daily_limits_client_named_check")
        ),
        sa.CheckConstraint("new_per_day >= 0", name=op.f("daily_limits_counted_check")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("daily_limits_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("daily_limits_pkey")),
        sa.UniqueConstraint("appended", name=op.f("daily_limits_appended_key")),
        sa.UniqueConstraint(
            "user_id", "client_id", name=op.f("daily_limits_user_id_client_id_key")
        ),
    )
    op.create_index(op.f("daily_limits_user_id_idx"), "daily_limits", ["user_id"], unique=False)
    op.create_table(
        "limit_raises",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("added", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("limit_raises_client_named_check")
        ),
        sa.CheckConstraint("added >= 1", name=op.f("limit_raises_counted_check")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("limit_raises_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("limit_raises_pkey")),
        sa.UniqueConstraint("appended", name=op.f("limit_raises_appended_key")),
        sa.UniqueConstraint(
            "user_id", "client_id", name=op.f("limit_raises_user_id_client_id_key")
        ),
    )
    op.create_index(op.f("limit_raises_user_id_idx"), "limit_raises", ["user_id"], unique=False)

    # by hand, since Alembic generates no trigger: `README.md`, Storage
    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON {table}"
            " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
        )


def downgrade() -> None:
    op.drop_index(op.f("limit_raises_user_id_idx"), table_name="limit_raises")
    op.drop_table("limit_raises")
    op.drop_index(op.f("daily_limits_user_id_idx"), table_name="daily_limits")
    op.drop_table("daily_limits")
