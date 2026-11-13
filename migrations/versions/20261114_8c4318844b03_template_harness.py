"""template_harness

Revision: 8c4318844b03
Revises: a8863bfc0c14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "8c4318844b03"
down_revision: str | Sequence[str] | None = "a8863bfc0c14"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "card_templates",
        sa.Column(
            "harness", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("card_templates", "harness")
