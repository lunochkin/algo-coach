"""one table for the settings

Revision: 07e5e40cdb57
Revises: 81baea624960
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "07e5e40cdb57"
down_revision: str | Sequence[str] | None = "81baea624960"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SETTING_NAME = postgresql.ENUM("new_per_day", "exam_size", name="setting_name", create_type=False)


def upgrade() -> None:
    # daily_limits never left a local database, so no record moves across
    op.drop_index(op.f("daily_limits_user_id_idx"), table_name="daily_limits")
    op.drop_table("daily_limits")

    SETTING_NAME.create(op.get_bind())
    op.create_table(
        "setting_changes",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", SETTING_NAME, nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "(name = 'new_per_day' AND value BETWEEN 0 AND 200)"
            " OR (name = 'exam_size' AND value BETWEEN 1 AND 500)",
            name=op.f("setting_changes_in_range_check"),
        ),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("setting_changes_client_named_check")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("setting_changes_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("setting_changes_pkey")),
        sa.UniqueConstraint("appended", name=op.f("setting_changes_appended_key")),
        sa.UniqueConstraint(
            "user_id", "client_id", name=op.f("setting_changes_user_id_client_id_key")
        ),
    )
    op.create_index(
        op.f("setting_changes_user_id_idx"), "setting_changes", ["user_id"], unique=False
    )

    # by hand, since Alembic generates no trigger: `README.md`, Storage
    op.execute(
        "CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON setting_changes"
        " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
    )


def downgrade() -> None:
    op.drop_index(op.f("setting_changes_user_id_idx"), table_name="setting_changes")
    op.drop_table("setting_changes")
    SETTING_NAME.drop(op.get_bind())

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
    op.execute(
        "CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON daily_limits"
        " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
    )
