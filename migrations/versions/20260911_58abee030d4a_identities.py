"""identities

Revision: 58abee030d4a
Revises: 9795c1b34d5d
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "58abee030d4a"
down_revision: str | Sequence[str] | None = "9795c1b34d5d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# created and dropped on its own, as the first migration's types are: the table
# would create it and never drop it
PROVIDER = postgresql.ENUM("google", "github", name="provider", create_type=False)


def upgrade() -> None:
    PROVIDER.create(op.get_bind())
    op.create_table(
        "identities",
        sa.Column("provider", PROVIDER, nullable=False),
        sa.Column("provider_user_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "provider_user_id <> ''", name=op.f("identities_provider_user_id_named_check")
        ),
        sa.CheckConstraint(
            "email = lower(email) AND email <> ''", name=op.f("identities_email_lowercased_check")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("identities_user_id_fkey")),
        sa.PrimaryKeyConstraint("provider", "provider_user_id", name=op.f("identities_pkey")),
    )
    op.create_index(op.f("identities_email_idx"), "identities", ["email"], unique=False)
    op.create_index(op.f("identities_user_id_idx"), "identities", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("identities_user_id_idx"), table_name="identities")
    op.drop_index(op.f("identities_email_idx"), table_name="identities")
    op.drop_table("identities")
    PROVIDER.drop(op.get_bind())
