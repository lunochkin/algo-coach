"""sessions

Revision: 1e426344edcb
Revises: 58abee030d4a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "1e426344edcb"
down_revision: str | Sequence[str] | None = "58abee030d4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expires_at > created_at", name=op.f("sessions_expires_after_it_starts_check")
        ),
        sa.CheckConstraint(
            "revoked_at >= created_at", name=op.f("sessions_revoked_after_it_starts_check")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("sessions_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("sessions_pkey")),
    )
    op.create_index(op.f("sessions_user_id_idx"), "sessions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("sessions_user_id_idx"), table_name="sessions")
    op.drop_table("sessions")
