import pytest
from fastapi.testclient import TestClient
from helpers import seed_problem

from algo_coach.api import create_app
from algo_coach.cards import CardStore
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, Card, RetirementReason, Selector, Template

USER = "u-4f9c2a"


@pytest.fixture
def client(tmp_path):
    seed_problem(tmp_path, id="p-greedy", techniques=["greedy", "sorting"])
    seed_problem(tmp_path, id="p-sorting", techniques=["sorting"])
    return TestClient(create_app(tmp_path, user_id=USER))


def attempted(root, id: str, *, user_id: str = USER, problem_id: str = "p-greedy") -> None:
    AttemptLog(root).append_attempt(
        Attempt(
            id=id,
            user_id=user_id,
            problem_id=problem_id,
            finished_at="2026-09-01T10:00:00Z",
            solved=True,
        )
    )


def test_the_board_offers_every_technique_a_served_problem_carries(client, tmp_path):
    """The first sitting opens on an empty log, and a board of attempted
    techniques alone would offer nothing to pick."""
    attempted(tmp_path, "a1", problem_id="p-sorting")

    board = client.get("/api/board").json()

    assert [(row["technique"], row["attempt_count"]) for row in board["rows"]] == [
        ("greedy", 0),
        ("sorting", 1),
    ]
    assert (board["ungrouped"], board["excluded"]) == (0, 0)


def test_the_board_counts_the_user_s_own_attempts_alone(client, tmp_path):
    attempted(tmp_path, "a1", user_id="u-b71e03")

    rows = client.get("/api/board").json()["rows"]

    assert {row["technique"]: row["attempt_count"] for row in rows} == {"greedy": 0, "sorting": 0}


def test_a_technique_s_cards_come_without_the_optional_template(client, tmp_path):
    """`content.md`: the optional template is surfaced on request alone."""
    templates = [
        Template(id="t1", slug="core", title="core", trigger="when", code="def f(): pass"),
        Template(
            id="t2", slug="hard", title="hard", trigger="when", code="def f(): pass", optional=True
        ),
    ]
    CardStore(tmp_path).put(
        Card(
            id="c1",
            slug="greedy-basic",
            technique="greedy",
            title="Greedy",
            trigger="a choice",
            brief="## Core idea",
            templates=templates,
            selector=Selector(technique="greedy", size=3),
        )
    )

    (card,) = client.get("/api/techniques/greedy/cards").json()

    assert [one["slug"] for one in card["templates"]] == ["core"]
    assert client.get("/api/techniques/sorting/cards").json() == []


def test_a_candidate_carries_no_statement(client):
    """The clock starts when the statement is served, so a statement in the
    list would be read untimed."""
    rows = client.get("/api/techniques/sorting/candidates").json()

    assert [row["problem_id"] for row in rows] == ["p-greedy", "p-sorting"]
    assert "statement" not in str(rows)


def test_a_retired_problem_is_not_a_candidate(client, tmp_path):
    ProblemStore(tmp_path).retire("p-greedy", RetirementReason.DEFECTIVE)

    rows = client.get("/api/techniques/sorting/candidates").json()

    assert [row["problem_id"] for row in rows] == ["p-sorting"]


def test_the_candidates_count_the_user_s_own_attempts_alone(client, tmp_path):
    attempted(tmp_path, "a1")
    attempted(tmp_path, "a2", user_id="u-b71e03")

    rows = client.get("/api/techniques/greedy/candidates").json()

    assert [row["attempt_count"] for row in rows] == [1]


def test_serving_the_statement_stores_the_sitting_for_the_user(client):
    """Serving writes the sitting, so the route is a POST though the loop reads
    the statement through it."""
    served = client.post("/api/problems/p-sorting/sittings").json()

    assert served["statement"] == "Given an array, return ..."
    assert (served["sitting"]["user_id"], served["sitting"]["problem_id"]) == (USER, "p-sorting")
    again = client.post("/api/problems/p-sorting/sittings").json()
    assert again["sitting"]["id"] == served["sitting"]["id"]


def test_serving_an_unknown_problem_is_not_found(client):
    assert client.post("/api/problems/nope/sittings").status_code == 404


def test_serving_a_retired_problem_is_refused(client, tmp_path):
    ProblemStore(tmp_path).retire("p-sorting", RetirementReason.DEFECTIVE)

    assert client.post("/api/problems/p-sorting/sittings").status_code == 409
