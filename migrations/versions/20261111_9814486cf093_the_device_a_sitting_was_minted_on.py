"""the device a sitting was minted on

Revision: 9814486cf093
Revises: cfde16cb60d4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9814486cf093"
down_revision: str | Sequence[str] | None = "cfde16cb60d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # absent on every sitting so far: none recorded where it was minted
    op.add_column("sittings", sa.Column("device", sa.Text(), nullable=True))
    op.create_check_constraint(op.f("sittings_device_named_check"), "sittings", "device <> ''")


def downgrade() -> None:
    op.drop_constraint(op.f("sittings_device_named_check"), "sittings", type_="check")
    op.drop_column("sittings", "device")
