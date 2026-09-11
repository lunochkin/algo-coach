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


def a_card(slug: str, technique: str, *, templates=None) -> Card:
    return Card(
        id=f"minted-{slug}",
        slug=slug,
        technique=technique,
        title=slug,
        trigger="a choice",
        brief="## Core idea",
        templates=templates
        or [Template(id=f"t-{slug}", slug="core", title="core", trigger="when", code="pass")],
        selector=Selector(technique=technique, size=3),
    )


def test_a_technique_s_cards_come_whole(client, tmp_path):
    """The optional template only says a card is covered without it, so the
    page receives it beside the core ones."""
    templates = [
        Template(id="t1", slug="core", title="core", trigger="when", code="def f(): pass"),
        Template(
            id="t2", slug="hard", title="hard", trigger="when", code="def f(): pass", optional=True
        ),
    ]
    CardStore(tmp_path).put(a_card("greedy-basic", "greedy", templates=templates))

    (card,) = client.get("/api/techniques/greedy/cards").json()

    assert [one["slug"] for one in card["templates"]] == ["core", "hard"]
    assert client.get("/api/techniques/sorting/cards").json() == []


def test_every_card_is_listed_by_technique_then_slug(client, tmp_path):
    """The cards list groups by technique, so the order it reads is that
    grouping."""
    store = CardStore(tmp_path)
    for slug, technique in (
        ("windows", "sliding-window"),
        ("on-answer", "binary-search"),
        ("basic", "binary-search"),
    ):
        store.put(a_card(slug, technique))

    listed = client.get("/api/cards").json()

    assert [(one["technique"], one["slug"]) for one in listed] == [
        ("binary-search", "basic"),
        ("binary-search", "on-answer"),
        ("sliding-window", "windows"),
    ]


def test_a_card_is_read_by_its_slug(client, tmp_path):
    """A re-seed keeps the slug, so a link to a card outlives the id the store
    minted."""
    CardStore(tmp_path).put(a_card("greedy-basic", "greedy"))

    assert client.get("/api/cards/greedy-basic").json()["id"] == "minted-greedy-basic"


def test_an_unknown_card_is_not_found(client):
    response = client.get("/api/cards/nope")

    assert (response.status_code, response.json()) == (404, {"detail": "no card nope"})


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


def test_a_served_sitting_is_read_back_by_its_id(client):
    """A reload of the sitting's page reaches the same statement and clock."""
    served = client.post("/api/problems/p-sorting/sittings").json()

    assert client.get(f"/api/sittings/{served['sitting']['id']}").json() == served


def test_another_user_s_sitting_is_not_found(client, tmp_path):
    sitting_id = client.post("/api/problems/p-sorting/sittings").json()["sitting"]["id"]
    other = TestClient(create_app(tmp_path, user_id="u-b71e03"))

    assert other.get(f"/api/sittings/{sitting_id}").status_code == 404
