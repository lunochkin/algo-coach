"""The native app's sign-in: a one-time code bound to a PKCE challenge, then a
token the app keeps. `README.md` gives the rules."""

import base64
import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel
from sqlalchemy import insert, select, update

from algo_coach.log.sessions import hashed
from algo_coach.log.table import app_codes, app_tokens
from algo_coach.storage import Database

CODE_LIFETIME = timedelta(minutes=5)
# a token unused this long signs nothing in. Each use extends it
IDLE = timedelta(days=90)


def issued(root: Database, user_id: str, challenge: str) -> str:
    """A code for the app that sent `challenge`. The table holds its hash."""
    code = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    with root.begin() as conn:
        conn.execute(
            insert(app_codes).values(
                id=hashed(code),
                user_id=user_id,
                challenge=challenge,
                created_at=now,
                expires_at=now + CODE_LIFETIME,
            )
        )
    return code


def exchanged(root: Database, code: str, verifier: str, device: str) -> str | None:
    """The app's token, where the code is live and unused and the verifier
    answers its challenge. Spends the code either way, so a wrong guess is
    the code's last."""
    now = datetime.now(UTC)
    with root.begin() as conn:
        spent = conn.execute(
            update(app_codes)
            .where(
                app_codes.c.id == hashed(code),
                app_codes.c.used_at.is_(None),
                app_codes.c.expires_at > now,
            )
            .values(used_at=now)
            .returning(app_codes.c.user_id, app_codes.c.challenge)
        ).first()
        if spent is None or spent.challenge != _challenge_of(verifier):
            return None
        token = secrets.token_urlsafe(32)
        conn.execute(
            insert(app_tokens).values(
                id=hashed(token),
                user_id=spent.user_id,
                device=device,
                created_at=now,
                last_used_at=now,
            )
        )
    return token


def app_user_of(root: Database, token: str) -> str | None:
    """The user an app token signs in as, extending the token by the use.
    `None` where it was revoked or went unused past `IDLE`."""
    now = datetime.now(UTC)
    with root.begin() as conn:
        return conn.execute(
            update(app_tokens)
            .where(
                app_tokens.c.id == hashed(token),
                app_tokens.c.revoked_at.is_(None),
                app_tokens.c.last_used_at > now - IDLE,
            )
            .values(last_used_at=now)
            .returning(app_tokens.c.user_id)
        ).scalar_one_or_none()


def app_revoked(root: Database, token: str) -> None:
    with root.begin() as conn:
        conn.execute(
            update(app_tokens)
            .where(app_tokens.c.id == hashed(token), app_tokens.c.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )


class SignedInApp(BaseModel):
    """A live app token as its owner sees it. The id is the token's hash, which
    signs nothing in."""

    id: str
    device: str
    created_at: datetime
    last_used_at: datetime


def signed_in_apps(root: Database, user_id: str) -> list[SignedInApp]:
    """The user's apps still signed in: neither revoked nor idle past `IDLE`."""
    live = (
        (app_tokens.c.user_id == user_id)
        & app_tokens.c.revoked_at.is_(None)
        & (app_tokens.c.last_used_at > datetime.now(UTC) - IDLE)
    )
    query = select(app_tokens).where(live).order_by(app_tokens.c.last_used_at.desc())
    with root.connect() as conn:
        return [SignedInApp.model_validate(dict(row)) for row in conn.execute(query).mappings()]


def app_revoked_by_id(root: Database, user_id: str, app_id: str) -> bool:
    """Revokes one of the user's own apps, `False` where none has the id."""
    with root.begin() as conn:
        mine = (app_tokens.c.id == app_id) & (app_tokens.c.user_id == user_id)
        found = conn.execute(
            update(app_tokens)
            .where(mine, app_tokens.c.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
            .returning(app_tokens.c.id)
        ).first()
    return found is not None


def _challenge_of(verifier: str) -> str:
    # S256, as RFC 7636 defines it: base64url of the SHA-256, unpadded
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
