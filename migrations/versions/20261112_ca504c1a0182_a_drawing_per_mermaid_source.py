"""a drawing per mermaid source

Revision: ca504c1a0182
Revises: 9814486cf093
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ca504c1a0182"
down_revision: str | Sequence[str] | None = "9814486cf093"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "diagrams",
        sa.Column("source_hash", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("tool", sa.Text(), nullable=False),
        sa.Column("light", sa.Text(), nullable=False),
        sa.Column("dark", sa.Text(), nullable=False),
        sa.Column("drawn_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("source_hash", name=op.f("diagrams_pkey")),
    )


def downgrade() -> None:
    op.drop_table("diagrams")
