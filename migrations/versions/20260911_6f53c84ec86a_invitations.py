"""invitations

Revision: 6f53c84ec86a
Revises: d60b4e1b2049
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "6f53c84ec86a"
down_revision: str | Sequence[str] | None = "d60b4e1b2049"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "invitations",
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "email = lower(email) AND email <> ''", name=op.f("invitations_email_lowercased_check")
        ),
        sa.PrimaryKeyConstraint("email", name=op.f("invitations_pkey")),
    )


def downgrade() -> None:
    op.drop_table("invitations")
