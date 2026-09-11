import pytest
from fastapi.testclient import TestClient
from helpers import PROVENANCE, seed_problem

from algo_coach.api import create_app
from algo_coach.cases import CaseLog
from algo_coach.mint import case

USER = "u-4f9c2a"
STATEMENT = "Double `n`.\n\n```python\ndef solve(n: int) -> int:\n```"
DOUBLE = "def solve(n):\n    return n * 2\n"
TRIPLE = "def solve(n):\n    return n * 3\n"


@pytest.fixture
def client(tmp_path):
    seed_problem(
        tmp_path, id="p1", techniques=["greedy", "sorting"], title="Double", statement=STATEMENT
    )
    for args, expected in (([1], 2), ([3], 6)):
        CaseLog(tmp_path).append(case("p1", args, expected, provenance=PROVENANCE))
    return TestClient(create_app(tmp_path, user_id=USER))


def ok(response):
    assert response.status_code == 200, response.text
    return response.json()


def test_one_sitting_runs_through_the_api_as_the_page_calls_it(client):
    """The page's calls, in the page's order, against one store: a route that
    wrote where the next one does not read fails here, so no step is left for a
    browser to find."""
    # the board offers the technique, and its candidates carry no statement
    board = ok(client.get("/api/board"))
    assert "greedy" in [row["technique"] for row in board["rows"]]
    (candidate,) = ok(client.get("/api/techniques/greedy/candidates"))
    assert (candidate["problem_id"], candidate["title"]) == ("p1", "Double")
    assert "statement" not in candidate

    # the press on the picked problem serves it, and a reload reads it back
    served = ok(client.post("/api/problems/p1/sittings"))
    sitting_id = served["sitting"]["id"]
    assert (served["statement"], served["signature"]) == (
        "Double `n`.",
        "def solve(n: int) -> int:",
    )
    assert ok(client.get(f"/api/sittings/{sitting_id}"))["sitting"] == served["sitting"]

    # a paused clock takes no submission until resumed
    assert (
        ok(client.post(f"/api/sittings/{sitting_id}/pause"))["sitting"]["pauses"][0]["until"]
        is None
    )
    submissions = f"/api/sittings/{sitting_id}/submissions"
    assert client.post(submissions, json={"code": DOUBLE}).status_code == 409
    ok(client.post(f"/api/sittings/{sitting_id}/resume"))

    # a wrong answer shows its first failing case whole, then a right one
    failing = ok(client.post(submissions, json={"code": TRIPLE}))
    assert failing["attempt"]["solved"] is False
    assert {key: failing["failure"][key] for key in ("args", "expected", "returned")} == {
        "args": [1],
        "expected": 2,
        "returned": 3,
    }
    passing = ok(client.post(submissions, json={"code": DOUBLE}))
    assert passing["attempt"]["solved"] is True and passing["failure"] is None
    assert [one["outcome"] for one in passing["verification"]["results"]] == ["passed", "passed"]

    # the end asks about each attempt over the problem's own techniques
    ended = ok(client.post(f"/api/sittings/{sitting_id}/end"))
    assert ended["sitting"]["ended_at"] is not None
    assert client.post(submissions, json={"code": DOUBLE}).status_code == 409
    asked = ok(client.get(f"/api/sittings/{sitting_id}/unclaimed"))
    assert asked["techniques"] == ["greedy", "sorting"]
    assert [one["id"] for one in asked["attempts"]] == [
        failing["attempt"]["id"],
        passing["attempt"]["id"],
    ]
    ok(
        client.post(
            f"/api/attempts/{failing['attempt']['id']}/claims",
            json={"declined": True, "confidence": "leaning"},
        )
    )
    ok(
        client.post(
            f"/api/attempts/{passing['attempt']['id']}/claims",
            json={"techniques": ["greedy"], "confidence": "sure"},
        )
    )
    assert ok(client.get(f"/api/sittings/{sitting_id}/unclaimed"))["attempts"] == []

    # the board counts what the claims resolved: the decline falls back to the
    # problem's techniques, and the claim names greedy alone
    rows = {row["technique"]: row for row in ok(client.get("/api/board"))["rows"]}
    assert (rows["greedy"]["attempt_count"], rows["greedy"]["solved_count"]) == (2, 1)
    assert (rows["sorting"]["attempt_count"], rows["sorting"]["solved_count"]) == (1, 0)
