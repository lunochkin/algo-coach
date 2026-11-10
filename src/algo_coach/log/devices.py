"""Every client signed in as one user: the browsers' sessions and the apps'
tokens, as both clients' account menus list them. `pages.md`, Sections."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel
from sqlalchemy import RowMapping, Table, select, update

from algo_coach.log.apps import IDLE
from algo_coach.log.sessions import hashed
from algo_coach.log.table import app_tokens, sessions
from algo_coach.storage import Database


class DeviceKind(StrEnum):
    BROWSER = "browser"
    APP = "app"


class SignedInDevice(BaseModel):
    """A live session or app token as its owner sees it. The id is the token's
    hash, which signs nothing in."""

    id: str
    kind: DeviceKind
    name: str | None  # an app's device name, or a browser's user agent
    created_at: datetime
    last_used_at: datetime
    current: bool  # the client that asks, which signs out rather than revokes


def signed_in_devices(
    root: Database, user_id: str, *, app_token: str | None, session_token: str | None
) -> list[SignedInDevice]:
    """The user's sessions and apps still signed in, most recently used first.
    The asking client's token marks its own row."""
    now = datetime.now(UTC)
    asking = hashed(app_token or session_token or "") if app_token or session_token else None
    with root.connect() as conn:
        browsers = conn.execute(
            select(sessions).where(
                sessions.c.user_id == user_id,
                sessions.c.revoked_at.is_(None),
                sessions.c.expires_at > now,
            )
        ).mappings()
        found = [_device(row, DeviceKind.BROWSER, row["user_agent"], asking) for row in browsers]
        apps = conn.execute(
            select(app_tokens).where(
                app_tokens.c.user_id == user_id,
                app_tokens.c.revoked_at.is_(None),
                app_tokens.c.last_used_at > now - IDLE,
            )
        ).mappings()
        found += [_device(row, DeviceKind.APP, row["device"], asking) for row in apps]
    return sorted(found, key=lambda one: one.last_used_at, reverse=True)


def _device(
    row: RowMapping, kind: DeviceKind, name: str | None, asking: str | None
) -> SignedInDevice:
    return SignedInDevice(
        id=row["id"],
        kind=kind,
        name=name,
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
        current=row["id"] == asking,
    )


TABLES: dict[DeviceKind, Table] = {DeviceKind.BROWSER: sessions, DeviceKind.APP: app_tokens}


def device_revoked(root: Database, user_id: str, kind: DeviceKind, device_id: str) -> bool:
    """Signs one of the user's clients out, `False` where none has the id."""
    table = TABLES[kind]
    with root.begin() as conn:
        found = conn.execute(
            update(table)
            .where(
                table.c.id == device_id, table.c.user_id == user_id, table.c.revoked_at.is_(None)
            )
            .values(revoked_at=datetime.now(UTC))
            .returning(table.c.id)
        ).first()
    return found is not None
