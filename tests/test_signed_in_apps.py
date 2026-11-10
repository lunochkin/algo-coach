from datetime import UTC, datetime, timedelta

from helpers import browsing
from sqlalchemy import update
from test_app_signin import CHALLENGE, VERIFIER

from algo_coach.log import exchanged, issued, named
from algo_coach.log.table import app_tokens

USER = "u-4f9c2a"
OTHER = "u-b71e03"


def app_for(database, user_id: str, device: str = "phone") -> str:
    named(database, user_id)
    found = exchanged(database, issued(database, user_id, CHALLENGE), VERIFIER, device)
    assert found is not None
    return found[0]


def listed(client) -> list[dict]:
    response = client.get("/api/apps")
    assert response.status_code == 200
    return response.json()


def test_the_account_lists_each_signed_in_app(database):
    app_for(database, USER, "phone")
    app_for(database, USER, "tablet")

    devices = [one["device"] for one in listed(browsing(database, USER))]

    assert sorted(devices) == ["phone", "tablet"]


def test_another_user_s_apps_are_not_listed(database):
    app_for(database, OTHER)

    assert listed(browsing(database, USER)) == []


def test_revoking_an_app_signs_it_out(database):
    """A lost phone is cut off from the web, not only by its own sign-out."""
    token = app_for(database, USER)
    client = browsing(database, USER)
    (app,) = listed(client)

    assert client.delete(f"/api/apps/{app['id']}").status_code == 204

    assert listed(client) == []
    snapshot = client.get("/api/knowledge/snapshot", headers={"authorization": f"Bearer {token}"})
    assert snapshot.status_code == 401


def test_another_user_s_app_cannot_be_revoked(database):
    app_for(database, OTHER)
    (theirs,) = listed(browsing(database, OTHER))

    assert browsing(database, USER).delete(f"/api/apps/{theirs['id']}").status_code == 404


def test_an_idle_app_is_no_longer_listed(database):
    app_for(database, USER)
    with database.begin() as conn:
        conn.execute(update(app_tokens).values(last_used_at=datetime.now(UTC) - timedelta(days=91)))

    assert listed(browsing(database, USER)) == []


def test_an_app_s_token_lists_and_revokes_apps(database):
    """A token reaches what a session reaches, the account's included:
    `README.md`."""
    token = app_for(database, USER)
    other = app_for(database, USER, device="tablet")
    client = browsing(database, USER)
    client.cookies.clear()
    bearer = {"authorization": f"Bearer {token}"}

    devices = {app["device"]: app["id"] for app in client.get("/api/apps", headers=bearer).json()}
    assert set(devices) == {"phone", "tablet"}
    assert client.delete(f"/api/apps/{devices['tablet']}", headers=bearer).status_code == 204
    cut_off = client.get("/api/knowledge/snapshot", headers={"authorization": f"Bearer {other}"})
    assert cut_off.status_code == 401
