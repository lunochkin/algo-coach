import pytest
from fastapi.testclient import TestClient
from helpers import PROVENANCE, seed_problem
from test_signed_in_apps import app_for

from algo_coach.api.app import create_app
from algo_coach.api.context import SESSION_COOKIE
from algo_coach.cases import CaseLog
from algo_coach.log import opened
from algo_coach.mint import case

USER = "u-4f9c2a"
DOUBLE = "def solve(n):\n    return n * 2\n"


@pytest.fixture
def phone(database) -> TestClient:
    """The native app: its bearer token, and no session cookie."""
    seed_problem(database, id="p1", techniques=["greedy"])
    CaseLog(database).append(case("p1", [1], 2, provenance=PROVENANCE))
    token = app_for(database, USER)
    headers = {"content-type": "application/json", "authorization": f"Bearer {token}"}
    return TestClient(create_app(database), headers=headers)


def test_the_token_reads_the_practice(phone):
    """The board, the problems and the cards are the user's own data."""
    for path in ("/api/board", "/api/problems", "/api/problems/p1", "/api/cards"):
        assert phone.get(path).status_code == 200, path


def test_the_token_opens_and_runs_a_sitting(phone):
    """A sitting writes to the log and runs code, as from the pages."""
    sitting = phone.post("/api/problems/p1/sittings").json()["sitting"]["id"]
    phone.post(f"/api/sittings/{sitting}/start")

    submitted = phone.post(f"/api/sittings/{sitting}/submissions", json={"code": DOUBLE})

    assert submitted.status_code == 200
    assert phone.get(f"/api/sittings/{sitting}").status_code == 200


def test_the_token_reads_the_account(phone):
    assert phone.get("/api/me").json()["user_id"] == USER


def test_the_token_syncs_the_knowledge_log(phone):
    synced = phone.post("/api/knowledge/sync", json={"device": "phone", "records": []})

    assert synced.json()["user_id"] == USER


def test_a_bad_token_is_refused_beside_a_good_session(database, phone):
    """A bearer token that names nobody fails, rather than falling back to the
    cookie the same request carries."""
    phone.headers["authorization"] = "Bearer not-a-token"
    phone.cookies.set(SESSION_COOKIE, opened(database, USER))

    assert phone.get("/api/board").status_code == 401
