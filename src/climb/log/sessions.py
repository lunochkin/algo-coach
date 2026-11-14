import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import insert, update

from climb.log.table import sessions
from climb.storage import Database

# how long a sign-in lasts before the user signs in again
LIFETIME = timedelta(days=30)


# a user agent is a label, so a long one is cut rather than stored whole
AGENT_LENGTH = 300


def opened(root: Database, user_id: str, user_agent: str | None = None) -> str:
    """A session for the user, returning the token its cookie carries. The
    table holds the token's hash alone."""
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    with root.begin() as conn:
        conn.execute(
            insert(sessions).values(
                id=hashed(token),
                user_id=user_id,
                created_at=now,
                expires_at=now + LIFETIME,
                last_used_at=now,
                user_agent=user_agent[:AGENT_LENGTH] if user_agent else None,
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
    """The user a token signs in as, marking the session used. `None` where no
    session carries the token, or its session expired or was revoked."""
    now = datetime.now(UTC)
    with root.begin() as conn:
        return conn.execute(
            update(sessions)
            .where(
                sessions.c.id == hashed(token),
                sessions.c.expires_at > now,
                sessions.c.revoked_at.is_(None),
            )
            .values(last_used_at=now)
            .returning(sessions.c.user_id)
        ).scalar_one_or_none()


def hashed(token: str) -> str:
    # unsalted: the token carries 256 random bits, which leaves nothing for a
    # salt to protect
    return hashlib.sha256(token.encode()).hexdigest()
