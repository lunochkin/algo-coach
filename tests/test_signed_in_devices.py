from datetime import UTC, datetime, timedelta

from helpers import browsing
from sqlalchemy import update
from test_app_signin import CHALLENGE, VERIFIER

from climb.api.context import SESSION_COOKIE
from climb.log import exchanged, issued, named, opened
from climb.log.table import app_tokens, sessions

USER = "u-4f9c2a"
OTHER = "u-b71e03"


def app_for(database, user_id: str, device: str = "phone") -> str:
    named(database, user_id)
    found = exchanged(database, issued(database, user_id, CHALLENGE), VERIFIER, device)
    assert found is not None
    return found[0]


def listed(client, **headers) -> list[dict]:
    response = client.get("/api/devices", headers=headers)
    assert response.status_code == 200
    return response.json()


def apps(client, **headers) -> list[dict]:
    return [one for one in listed(client, **headers) if one["kind"] == "app"]


def bearer(token: str) -> dict:
    return {"authorization": f"Bearer {token}"}


def test_the_account_lists_each_signed_in_app(database):
    app_for(database, USER, "phone")
    app_for(database, USER, "tablet")

    assert sorted(one["name"] for one in apps(browsing(database, USER))) == ["phone", "tablet"]


def test_another_user_s_devices_are_not_listed(database):
    app_for(database, OTHER)
    opened(database, OTHER)

    assert [one["kind"] for one in listed(browsing(database, USER))] == ["browser"]


def test_revoking_an_app_signs_it_out(database):
    """A lost phone is cut off from any other client, not only by its own
    sign-out."""
    token = app_for(database, USER)
    client = browsing(database, USER)
    (app,) = apps(client)

    assert client.delete(f"/api/devices/app/{app['id']}").status_code == 204

    assert apps(client) == []
    assert client.get("/api/knowledge/snapshot", headers=bearer(token)).status_code == 401


def test_another_user_s_device_cannot_be_revoked(database):
    app_for(database, OTHER)
    (theirs,) = apps(browsing(database, OTHER))

    assert browsing(database, USER).delete(f"/api/devices/app/{theirs['id']}").status_code == 404


def test_an_idle_app_is_no_longer_listed(database):
    app_for(database, USER)
    with database.begin() as conn:
        conn.execute(update(app_tokens).values(last_used_at=datetime.now(UTC) - timedelta(days=91)))

    assert apps(browsing(database, USER)) == []


def test_the_list_marks_the_app_that_asks(database):
    """The asking phone signs out from its own row, rather than revoking its
    token past the outbox."""
    token = app_for(database, USER)
    app_for(database, USER, device="tablet")
    client = browsing(database, USER)
    client.cookies.clear()

    marked = {one["name"]: one["current"] for one in apps(client, **bearer(token))}

    assert marked == {"phone": True, "tablet": False}


def test_a_browser_lists_itself_marked(database):
    """A browser is a signed-in device as an app is, named by its own agent."""
    app_for(database, USER)
    client = browsing(database, USER)
    client.cookies.set(SESSION_COOKIE, opened(database, USER, "Firefox/150.0"))

    (me,) = [one for one in listed(client) if one["current"]]

    assert (me["kind"], me["name"]) == ("browser", "Firefox/150.0")
    assert [one["current"] for one in apps(client)] == [False]


def test_a_phone_signs_a_browser_out(database):
    """A browser left signed in on another computer is cut off by the phone."""
    token = app_for(database, USER)
    left = opened(database, USER)
    phone = browsing(database, USER)
    phone.cookies.clear()
    browsers = [one for one in listed(phone, **bearer(token)) if one["kind"] == "browser"]

    for one in browsers:
        revoked = phone.delete(f"/api/devices/browser/{one['id']}", headers=bearer(token))
        assert revoked.status_code == 204

    phone.cookies.set(SESSION_COOKIE, left)
    assert phone.get("/api/me").status_code == 401


def test_a_session_records_its_last_use(database):
    client = browsing(database, USER)
    with database.begin() as conn:
        conn.execute(update(sessions).values(last_used_at=datetime.now(UTC) - timedelta(days=3)))

    client.get("/api/me")

    (me,) = listed(client)
    assert datetime.fromisoformat(me["last_used_at"]) > datetime.now(UTC) - timedelta(minutes=1)
