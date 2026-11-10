"""a subtopic's title

Revision: f326fd1871e5
Revises: a0b4acac72f2
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f326fd1871e5"
down_revision: str | Sequence[str] | None = "a0b4acac72f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("subtopics", sa.Column("title", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("subtopics", "title")
