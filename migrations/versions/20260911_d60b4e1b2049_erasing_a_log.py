"""erasing a log

Revision: d60b4e1b2049
Revises: 1e426344edcb
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d60b4e1b2049"
down_revision: str | Sequence[str] | None = "1e426344edcb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # a delete passes where the transaction set `algo_coach.erasing`, which one
    # user's whole log being erased does: `log.md`. An update never passes
    op.execute(
        """
        CREATE OR REPLACE FUNCTION refuse_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'DELETE' AND current_setting('algo_coach.erasing', true) = 'on' THEN
                RETURN NULL;
            END IF;
            RAISE EXCEPTION '% is append-only: % refused', TG_TABLE_NAME, TG_OP;
        END
        $$
        """
    )


def downgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION refuse_rewrite() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION '% is append-only: % refused', TG_TABLE_NAME, TG_OP;
        END
        $$
        """
    )
