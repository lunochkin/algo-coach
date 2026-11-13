"""the_screen_site

Revision: f59f7d65cc9f
Revises: add978a5c77a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f59f7d65cc9f"
down_revision: str | Sequence[str] | None = "add978a5c77a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # placed where the code lists them, since a sort over the type follows it
    op.execute("ALTER TYPE call_site ADD VALUE 'screen' AFTER 'generator'")
    op.execute("ALTER TYPE writing_state ADD VALUE 'screened' AFTER 'checked'")
    op.execute("ALTER TYPE gate ADD VALUE 'copied' AFTER 'no_value'")
    op.add_column("drafts", sa.Column("screen_call_id", sa.Text(), nullable=True))
    op.create_foreign_key(
        op.f("drafts_screen_call_id_fkey"), "drafts", "calls", ["screen_call_id"], ["id"]
    )


def downgrade() -> None:
    # Postgres drops no enum value, so the three added above stay
    op.drop_constraint(op.f("drafts_screen_call_id_fkey"), "drafts", type_="foreignkey")
    op.drop_column("drafts", "screen_call_id")
