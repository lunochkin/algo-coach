from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from algo_coach.api import Root, UserId, create_app
from algo_coach.api.context import SESSION_COOKIE
from algo_coach.log import hashed, named, opened
from algo_coach.log.table import sessions
from algo_coach.sitting import Missing, Refused

USER = "u-4f9c2a"


written: list[bool] = []


@pytest.fixture(autouse=True)
def nothing_written():
    written.clear()


@pytest.fixture
def client(database):
    app = create_app(database)

    @app.get("/whose")
    def whose(root: Root, user_id: UserId) -> dict[str, str]:
        return {"database": str(root.engine.url.database), "user_id": user_id}

    @app.get("/missing")
    def missing() -> None:
        raise Missing("no sitting s1")

    @app.get("/refused")
    def refused() -> None:
        raise Refused("sitting s1 is paused")

    @app.get("/broken")
    def broken() -> None:
        raise ValueError("a stored record the engine wrote wrong")

    @app.post("/write")
    def write() -> dict[str, bool]:
        written.append(True)
        return {"written": True}

    return TestClient(app, raise_server_exceptions=False)


def signed_in(client, database, user_id: str = USER) -> str:
    """Opens a session for the user and sets its token on the client."""
    named(database, user_id)
    token = opened(database, user_id)
    client.cookies.set(SESSION_COOKIE, token)
    return token


def test_a_route_reads_the_user_from_the_session_its_cookie_names(client, database):
    """The user is the session's, so two browsers signed in as two users read
    two logs through one app."""
    signed_in(client, database)

    assert client.get("/whose").json() == {
        "database": database.engine.url.database,
        "user_id": USER,
    }


def test_a_request_with_no_session_is_not_signed_in(client):
    response = client.get("/whose")

    assert (response.status_code, response.json()) == (401, {"detail": "not signed in"})


def test_a_token_no_session_carries_is_not_signed_in(client, database):
    signed_in(client, database)
    client.cookies.set(SESSION_COOKIE, "a-token-nobody-was-given")

    assert client.get("/whose").status_code == 401


def test_a_revoked_session_signs_nobody_in(client, database):
    """A stored session ends when it is revoked, where a signed token would
    stand until it expired: `README.md`."""
    token = signed_in(client, database)
    with database.begin() as conn:
        conn.execute(
            update(sessions)
            .where(sessions.c.id == hashed(token))
            .values(revoked_at=datetime.now(UTC))
        )

    assert client.get("/whose").status_code == 401


def test_an_expired_session_signs_nobody_in(client, database):
    token = signed_in(client, database)
    with database.begin() as conn:
        # created further back than the session lasts, so it has expired
        conn.execute(
            update(sessions)
            .where(sessions.c.id == hashed(token))
            .values(
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
                expires_at=datetime(2026, 1, 31, tzinfo=UTC),
            )
        )

    assert client.get("/whose").status_code == 401


@pytest.mark.parametrize(
    "content_type", ["application/x-www-form-urlencoded", "multipart/form-data", "text/plain"]
)
def test_a_write_a_form_can_send_is_refused_before_the_route_runs(client, content_type):
    """A form on another site sends one of these, with the session cookie, and
    a route that ran it would write as the signed-in user."""
    response = client.post("/write", content=b"a=1", headers={"content-type": content_type})

    assert response.status_code == 415
    assert written == []


def test_a_write_with_no_content_type_is_refused(client):
    """A body-less request from another site sends no content type either."""
    assert client.post("/write").status_code == 415
    assert written == []


@pytest.mark.parametrize("content_type", ["application/json", "Application/JSON; charset=utf-8"])
def test_a_json_write_reaches_its_route(client, content_type):
    assert client.post("/write", headers={"content-type": content_type}).status_code == 200
    assert written == [True]


def test_a_read_needs_no_content_type(client):
    assert client.get("/missing").status_code == 404


def test_a_route_that_names_no_user_needs_no_session(client):
    """The cards are product data, read by anyone the pages reach."""
    assert client.get("/api/cards").status_code == 200


def test_a_record_the_user_cannot_reach_answers_not_found(client):
    """Another user's sitting reads as missing in the domain, and the status
    says the same."""
    response = client.get("/missing")

    assert (response.status_code, response.json()) == (404, {"detail": "no sitting s1"})


def test_a_move_the_state_refuses_answers_conflict_with_the_domain_s_reason(client):
    """The frontend shows the domain's own sentence rather than a status it
    has to translate."""
    response = client.get("/refused")

    assert (response.status_code, response.json()) == (409, {"detail": "sitting s1 is paused"})


def test_any_other_value_error_stays_a_server_error(client):
    """A `ValueError` is also what pydantic and a store raise on a defect, and
    a corrupt record read as the request's fault would hide the engine's bug."""
    assert client.get("/broken").status_code == 500
