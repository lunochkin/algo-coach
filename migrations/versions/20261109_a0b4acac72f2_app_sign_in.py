"""app sign in

Revision: a0b4acac72f2
Revises: aeb1f4b74958
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a0b4acac72f2"
down_revision: str | Sequence[str] | None = "aeb1f4b74958"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "app_codes",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("challenge", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expires_at > created_at", name=op.f("app_codes_expires_after_it_starts_check")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("app_codes_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("app_codes_pkey")),
    )
    op.create_table(
        "app_tokens",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("device <> ''", name=op.f("app_tokens_device_named_check")),
        sa.CheckConstraint(
            "revoked_at >= created_at", name=op.f("app_tokens_revoked_after_it_starts_check")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("app_tokens_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("app_tokens_pkey")),
    )
    op.create_index(op.f("app_tokens_user_id_idx"), "app_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("app_tokens_user_id_idx"), table_name="app_tokens")
    op.drop_table("app_tokens")
    op.drop_table("app_codes")
