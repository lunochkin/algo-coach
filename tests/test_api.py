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
