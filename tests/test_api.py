import pytest
from fastapi.testclient import TestClient

from algo_coach.api import Root, UserId, create_app
from algo_coach.sitting import Missing, Refused


@pytest.fixture
def client(database):
    app = create_app(database, user_id="u-4f9c2a")

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


def test_a_route_reads_the_database_and_the_user_the_app_was_built_with(client, database):
    """One user stands in for authentication, and a route takes neither from
    the request."""
    assert client.get("/whose").json() == {
        "database": database.engine.url.database,
        "user_id": "u-4f9c2a",
    }


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
