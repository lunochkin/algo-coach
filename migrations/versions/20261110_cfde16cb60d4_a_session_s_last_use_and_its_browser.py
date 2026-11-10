"""a session's last use and its browser

Revision: cfde16cb60d4
Revises: 07e5e40cdb57
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cfde16cb60d4"
down_revision: str | Sequence[str] | None = "07e5e40cdb57"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # a session open before this one was last used no later than it was opened,
    # as far as anything recorded says, so its opening stands in
    op.add_column("sessions", sa.Column("last_used_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE sessions SET last_used_at = created_at")
    op.alter_column("sessions", "last_used_at", nullable=False)
    op.add_column("sessions", sa.Column("user_agent", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "user_agent")
    op.drop_column("sessions", "last_used_at")
