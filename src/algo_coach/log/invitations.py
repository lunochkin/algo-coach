"""The emails allowed to sign in, matched lowercased as an identity's are."""

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert

from algo_coach.log.table import invitations
from algo_coach.storage import Database


def invite(root: Database, email: str) -> None:
    """Lets the email sign in. Inviting it again changes nothing."""
    with root.begin() as conn:
        conn.execute(
            insert(invitations)
            .values(email=email.lower(), created_at=func.now())
            .on_conflict_do_nothing()
        )


def withdraw(root: Database, email: str) -> bool:
    """Stops the email signing in again. `False` where it was never invited."""
    with root.begin() as conn:
        removed = conn.execute(delete(invitations).where(invitations.c.email == email.lower()))
    return removed.rowcount > 0


def invited(root: Database, email: str) -> bool:
    query = select(invitations.c.email).where(invitations.c.email == email.lower())
    with root.connect() as conn:
        return conn.execute(query).first() is not None


def invitations_held(root: Database) -> list[str]:
    query = select(invitations.c.email).order_by(invitations.c.email)
    with root.connect() as conn:
        return list(conn.execute(query).scalars())
