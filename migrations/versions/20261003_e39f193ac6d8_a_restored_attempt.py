"""a restored attempt

Revision: e39f193ac6d8
Revises: 0bd2109b024e
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e39f193ac6d8"
down_revision: str | Sequence[str] | None = "0bd2109b024e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("attempts", sa.Column("restored", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("attempts", "restored")
