from fastapi.testclient import TestClient
from helpers import browsing
from sqlalchemy import select

from algo_coach.api import create_app
from algo_coach.api.context import SESSION_COOKIE
from algo_coach.api.signin import Client, SignIn
from algo_coach.log import Provider
from algo_coach.log.table import sessions
from algo_coach.storage import Database

USER = "u-4f9c2a"


def test_the_login_page_is_offered_every_configured_provider():
    """Read before anyone signs in, so the route needs no session."""
    clients = {
        Provider.GOOGLE: Client("google-id", "s"),
        Provider.GITHUB: Client("github-id", "s"),
    }
    app = create_app(Database(), sign_in=SignIn("http://localhost:5173", "a-key", clients))

    offered = TestClient(app).get("/api/sign-in").json()

    assert offered == {"providers": ["google", "github"], "dev_login": None}


def test_the_login_page_is_offered_the_dev_login_and_its_user():
    offered = TestClient(create_app(Database(), dev_login="local")).get("/api/sign-in").json()

    assert offered == {"providers": [], "dev_login": "local"}


def test_signing_out_revokes_the_session_and_clears_its_cookie(database):
    """Revoked on the server: a copy of the cookie kept elsewhere signs nobody
    in after the browser signed out."""
    client = browsing(database, USER)
    token = client.cookies[SESSION_COOKIE]

    response = client.delete("/api/session")

    assert response.status_code == 204
    assert 'session=""' in response.headers["set-cookie"]
    with database.connect() as conn:
        assert conn.execute(select(sessions.c.revoked_at)).scalar_one() is not None
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get("/api/board").status_code == 401


def test_signing_out_without_a_session_still_answers(database):
    """A browser whose session already expired signs out as any other does."""
    client = TestClient(create_app(database), headers={"content-type": "application/json"})

    assert client.delete("/api/session").status_code == 204


def test_signing_out_is_a_write_another_site_cannot_forge(database):
    """A form posting to sign the user out is refused as any other write is."""
    client = browsing(database, USER)

    response = client.delete("/api/session", headers={"content-type": "text/plain"})

    assert response.status_code == 415
    assert client.get("/api/board").status_code == 200
