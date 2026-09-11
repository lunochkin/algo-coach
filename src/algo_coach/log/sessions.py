import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import insert, select, update

from algo_coach.log.table import sessions
from algo_coach.storage import Database

# how long a sign-in lasts before the user signs in again
LIFETIME = timedelta(days=30)


def opened(root: Database, user_id: str) -> str:
    """A session for the user, returning the token its cookie carries. The
    table holds the token's hash alone."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    with root.begin() as conn:
        conn.execute(
            insert(sessions).values(
                id=hashed(token), user_id=user_id, created_at=now, expires_at=now + LIFETIME
            )
        )
    return token


def revoked(root: Database, token: str) -> None:
    """Ends the session the token carries, where one is still open."""
    with root.begin() as conn:
        conn.execute(
            update(sessions)
            .where(sessions.c.id == hashed(token), sessions.c.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )


def user_of(root: Database, token: str) -> str | None:
    """The user a token signs in as. `None` where no session carries the token,
    or its session expired or was revoked."""
    with root.connect() as conn:
        return conn.execute(
            select(sessions.c.user_id).where(
                sessions.c.id == hashed(token),
                sessions.c.expires_at > datetime.now(UTC),
                sessions.c.revoked_at.is_(None),
            )
        ).scalar_one_or_none()


def hashed(token: str) -> str:
    # unsalted: the token carries 256 random bits, which leaves nothing for a
    # salt to protect
    return hashlib.sha256(token.encode()).hexdigest()
