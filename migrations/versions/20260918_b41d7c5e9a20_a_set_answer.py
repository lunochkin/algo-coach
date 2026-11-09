"""a template whose answer is a set

Revision: b41d7c5e9a20
Revises: c3f81a06de47
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b41d7c5e9a20"
down_revision: str | Sequence[str] | None = "c3f81a06de47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "card_templates",
        sa.Column("unordered", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("card_templates", "unordered")
