import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from algo_coach.api import create_app
from algo_coach.api.__main__ import app as served
from algo_coach.api.context import SESSION_COOKIE
from algo_coach.api.signin import Client, SignIn
from algo_coach.log import Provider, hashed
from algo_coach.log.table import sessions, users
from algo_coach.storage import Database


def browser(root, user: str = "local", host: str = "127.0.0.1") -> TestClient:
    app = create_app(root, dev_login=user)
    return TestClient(app, base_url=f"http://{host}", follow_redirects=False)


def test_the_dev_login_signs_in_as_the_user_the_flag_names(database):
    """The records written under `local` are the author's, so the dev login
    reaches them with no provider."""
    response = browser(database).get("/api/auth/dev")

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    with database.connect() as conn:
        (session,) = conn.execute(select(sessions.c.id, sessions.c.user_id))
        assert conn.execute(select(users.c.id)).scalars().all() == ["local"]
    assert tuple(session) == (hashed(response.cookies[SESSION_COOKIE]), "local")


def test_the_dev_login_s_cookie_signs_later_requests_in(database):
    """The session the dev login opens is the one every route reads, as a
    provider's sign-in is."""
    client = browser(database, user="u-4f9c2a")
    client.get("/api/auth/dev")

    assert client.get("/api/board").status_code == 200


def test_a_user_the_log_already_names_signs_in_as_itself(database):
    client = browser(database, user="u-4f9c2a")
    client.get("/api/auth/dev")

    assert client.get("/api/auth/dev").status_code == 303
    with database.connect() as conn:
        assert conn.execute(select(users.c.id)).scalars().all() == ["u-4f9c2a"]


def test_the_dev_login_answers_only_a_request_that_arrived_on_loopback(database):
    """Another machine's request never arrives at 127.0.0.1, however the server
    is bound, so the flag set on a reachable server opens nothing."""
    response = browser(database, host="10.41.4.64").get("/api/auth/dev")

    assert response.status_code == 403
    with database.connect() as conn:
        assert conn.execute(select(sessions.c.id)).all() == []


def test_the_dev_login_is_absent_without_its_flag():
    client = TestClient(create_app(Database()), base_url="http://127.0.0.1")

    assert client.get("/api/auth/dev").status_code == 404


def test_the_dev_login_refuses_to_start_beside_a_provider_s_client():
    """A deployed engine signs its users in through a provider, so a client
    configured beside the flag is a deployment the flag would open."""
    sign_in = SignIn("https://coach.example", "a-key", {Provider.GITHUB: Client("id", "s")})

    with pytest.raises(ValueError, match="dev login"):
        create_app(Database(), sign_in=sign_in, dev_login="local")


def test_the_served_app_signs_in_as_the_user_the_environment_names(monkeypatch):
    monkeypatch.setenv("ALGO_COACH_DEV_LOGIN", "u-4f9c2a")

    app = served()

    assert app.state.dev_user == "u-4f9c2a"


def test_an_empty_flag_enables_nothing(monkeypatch):
    """A line left as `ALGO_COACH_DEV_LOGIN=` in `.env` names no user."""
    monkeypatch.setenv("ALGO_COACH_DEV_LOGIN", "")
    client = TestClient(served(), base_url="http://127.0.0.1")

    assert client.get("/api/auth/dev").status_code == 404
