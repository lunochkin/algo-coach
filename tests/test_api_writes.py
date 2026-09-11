import pytest
from fastapi.testclient import TestClient
from helpers import PROVENANCE, seed_problem

from algo_coach.api import create_app
from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog
from algo_coach.mint import case

USER = "u-4f9c2a"
DOUBLE = "def solve(n):\n    return n * 2\n"
TRIPLE = "def solve(n):\n    return n * 3\n"


@pytest.fixture
def root(tmp_path):
    seed_problem(tmp_path, id="p1", techniques=["greedy", "sorting"])
    for args, expected in (([1], 2), ([3], 6)):
        CaseLog(tmp_path).append(case("p1", args, expected, provenance=PROVENANCE))
    return tmp_path


@pytest.fixture
def client(root):
    return TestClient(create_app(root, user_id=USER))


@pytest.fixture
def sitting_id(client) -> str:
    return client.post("/problems/p1/sittings").json()["sitting"]["id"]


def submitted(client, sitting_id: str, code: str = DOUBLE):
    return client.post(f"/sittings/{sitting_id}/submissions", json={"code": code})


def test_a_submission_answers_with_its_verdict_per_case(client, sitting_id, root):
    """The verdict is shown beside the editor, so the response carries it
    rather than a second request."""
    body = submitted(client, sitting_id, TRIPLE).json()

    assert body["attempt"]["solved"] is False
    assert [one["outcome"] for one in body["verification"]["results"]] == ["wrong", "wrong"]
    assert [one.id for one in AttemptLog(root).attempts()] == [body["attempt"]["id"]]


def test_a_verdict_carries_no_expected_value(client, sitting_id):
    """The answers stay server-side, or a response is the case set."""
    (result, _) = submitted(client, sitting_id, TRIPLE).json()["verification"]["results"]

    assert set(result) == {"case_id", "outcome", "elapsed_ms", "error"}


def test_a_failing_submission_shows_the_first_failing_case_whole(client, sitting_id):
    failure = submitted(client, sitting_id, TRIPLE).json()["failure"]

    assert failure == {
        "case_id": failure["case_id"],
        "outcome": "wrong",
        "args": [1],
        "expected": 2,
        "returned": 3,
        "error": None,
    }


def test_a_crashing_submission_shows_what_raised(client, sitting_id):
    """A crash with no message leaves the solver guessing which line raised."""
    raising = "def solve(n):\n    return [n][1]\n"

    failure = submitted(client, sitting_id, raising).json()["failure"]

    assert failure["outcome"] == "crashed"
    assert "line 2, in solve" in failure["error"] and "IndexError" in failure["error"]


def test_a_submission_without_code_is_unprocessable(client, sitting_id):
    assert client.post(f"/sittings/{sitting_id}/submissions", json={}).status_code == 422


def test_a_paused_sitting_refuses_a_submission_until_resumed(client, sitting_id):
    """A submission while paused would stamp a time the clock was not
    counting."""
    assert client.post(f"/sittings/{sitting_id}/pause").json()["pauses"][0]["until"] is None
    assert submitted(client, sitting_id).status_code == 409

    assert client.post(f"/sittings/{sitting_id}/resume").json()["pauses"][0]["until"] is not None
    assert submitted(client, sitting_id).status_code == 200


def test_pausing_twice_is_refused_with_the_domain_s_reason(client, sitting_id):
    client.post(f"/sittings/{sitting_id}/pause")

    response = client.post(f"/sittings/{sitting_id}/pause")

    assert (response.status_code, response.json()["detail"]) == (
        409,
        f"sitting {sitting_id} is already paused",
    )


def test_an_ended_sitting_takes_no_submission(client, sitting_id):
    """The loop ends a sitting on its claim, and a sitting left open reports an
    elapsed time that moves with the moment it is read."""
    assert client.post(f"/sittings/{sitting_id}/end").json()["ended_at"] is not None

    assert submitted(client, sitting_id).status_code == 409


def test_another_user_s_sitting_is_not_found(root, sitting_id):
    other = TestClient(create_app(root, user_id="u-b71e03"))

    assert other.post(f"/sittings/{sitting_id}/pause").status_code == 404
    assert submitted(other, sitting_id).status_code == 404


def test_each_attempt_of_the_sitting_is_asked_about_until_claimed(client, sitting_id):
    """A drill can mint several attempts, and a claim on the last alone leaves
    the earlier ones to the problem's techniques."""
    first = submitted(client, sitting_id, TRIPLE).json()["attempt"]["id"]
    second = submitted(client, sitting_id).json()["attempt"]["id"]
    assert [one["id"] for one in client.get(f"/sittings/{sitting_id}/unclaimed").json()] == [
        first,
        second,
    ]

    written = client.post(
        f"/attempts/{first}/claims", json={"techniques": ["sorting"], "confidence": "sure"}
    ).json()

    assert (written["techniques"], written["source"]) == (["sorting"], "user")
    assert [one["id"] for one in client.get(f"/sittings/{sitting_id}/unclaimed").json()] == [second]


def test_a_claim_is_limited_to_the_problem_s_own_techniques(client, sitting_id):
    """The candidates are the problem's derived techniques, which the route
    loads rather than the page sending them."""
    attempt_id = submitted(client, sitting_id).json()["attempt"]["id"]

    response = client.post(
        f"/attempts/{attempt_id}/claims", json={"techniques": ["trie"], "confidence": "guess"}
    )

    assert response.status_code == 409
    assert "trie" in response.json()["detail"]


def test_a_claim_naming_nothing_is_refused_and_a_decline_is_not(client, sitting_id):
    attempt_id = submitted(client, sitting_id).json()["attempt"]["id"]
    route = f"/attempts/{attempt_id}/claims"

    assert client.post(route, json={"confidence": "sure"}).status_code == 409
    assert client.post(route, json={"confidence": "sure", "declined": True}).status_code == 200


def test_claiming_another_user_s_attempt_is_not_found(root, client, sitting_id):
    attempt_id = submitted(client, sitting_id).json()["attempt"]["id"]
    other = TestClient(create_app(root, user_id="u-b71e03"))

    response = other.post(
        f"/attempts/{attempt_id}/claims", json={"techniques": ["greedy"], "confidence": "sure"}
    )

    assert response.status_code == 404
