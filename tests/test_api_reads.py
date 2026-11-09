import pytest
from helpers import browsing, seed_problem

from algo_coach.cards import CardStore
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, Card, RetirementReason, Selector, Template

USER = "u-4f9c2a"


@pytest.fixture
def client(database):
    seed_problem(database, id="p-greedy", techniques=["greedy", "sorting"])
    seed_problem(database, id="p-sorting", techniques=["sorting"])
    return browsing(database, USER)


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


def test_the_board_offers_every_technique_a_served_problem_carries(client, database):
    """The first sitting opens on an empty log, and a board of attempted
    techniques alone would offer nothing to pick."""
    attempted(database, "a1", problem_id="p-sorting")

    board = client.get("/api/board").json()

    assert [(row["technique"], row["attempt_count"]) for row in board["rows"]] == [
        ("greedy", 0),
        ("sorting", 1),
    ]
    assert (board["ungrouped"], board["excluded"]) == (0, 0)


def test_the_board_counts_the_user_s_own_attempts_alone(client, database):
    attempted(database, "a1", user_id="u-b71e03")

    rows = client.get("/api/board").json()["rows"]

    assert {row["technique"]: row["attempt_count"] for row in rows} == {"greedy": 0, "sorting": 0}


def test_a_sitting_with_no_submission_counts_for_nothing(client):
    """Opening a problem serves it, so a sitting nobody submitted to records
    that the user looked, not that they tried."""
    client.post("/api/problems/p-sorting/sittings")

    rows = client.get("/api/board").json()["rows"]
    candidates = client.get("/api/techniques/sorting/candidates").json()

    assert {row["technique"]: row["attempt_count"] for row in rows} == {"greedy": 0, "sorting": 0}
    assert {row["problem_id"]: row["attempt_count"] for row in candidates} == {
        "p-greedy": 0,
        "p-sorting": 0,
    }


def test_an_untimed_attempt_counts_by_its_verdict(client, database):
    """A clock nobody started says nothing about speed, and the solve still
    counts."""
    attempted(database, "a1", problem_id="p-sorting")
    assert AttemptLog(database).attempts(USER)[0].time_to_solve_sec is None

    (row,) = [
        one for one in client.get("/api/board").json()["rows"] if one["technique"] == "sorting"
    ]

    assert (row["attempt_count"], row["solved_count"]) == (1, 1)


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


def test_a_technique_s_cards_come_whole(client, database):
    """The optional template only says a card is covered without it, so the
    page receives it beside the core ones."""
    templates = [
        Template(id="t1", slug="core", title="core", trigger="when", code="def f(): pass"),
        Template(
            id="t2", slug="hard", title="hard", trigger="when", code="def f(): pass", optional=True
        ),
    ]
    CardStore(database).put(a_card("greedy-basic", "greedy", templates=templates))

    (card,) = client.get("/api/techniques/greedy/cards").json()

    assert [one["slug"] for one in card["templates"]] == ["core", "hard"]
    assert client.get("/api/techniques/sorting/cards").json() == []


def test_every_card_is_listed_by_technique_then_slug(client, database):
    """The cards list groups by technique, so the order it reads is that
    grouping."""
    store = CardStore(database)
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


def test_a_card_is_listed_under_the_family_its_technique_belongs_to(client, database):
    """Knapsack is a kind of DP, so its card is read beside the DP cards
    rather than apart from them."""
    store = CardStore(database)
    for slug, technique in (
        ("knapsack-01", "knapsack"),
        ("windows", "sliding-window"),
        ("linear", "dynamic-programming"),
    ):
        store.put(a_card(slug, technique))

    listed = client.get("/api/cards").json()

    assert [(one["family"], one["slug"]) for one in listed] == [
        ("dynamic-programming", "linear"),
        ("dynamic-programming", "knapsack-01"),
        ("sliding-window", "windows"),
    ]


def test_a_technique_s_cards_include_its_narrower_techniques(client, database):
    """The DP page offers the knapsack card, since solving knapsack is
    practising DP. Granularity follows teaching, so one technique carries
    several cards."""
    store = CardStore(database)
    for slug, technique in (
        ("linear", "dynamic-programming"),
        ("knapsack-01", "knapsack"),
        ("windows", "sliding-window"),
    ):
        store.put(a_card(slug, technique))

    listed = client.get("/api/techniques/dynamic-programming/cards").json()

    assert [one["slug"] for one in listed] == ["knapsack-01", "linear"]


def test_a_card_is_read_by_its_slug(client, database):
    """A re-seed keeps the slug, so a link to a card outlives the id the store
    minted."""
    CardStore(database).put(a_card("greedy-basic", "greedy"))

    studied = client.get("/api/cards/greedy-basic").json()

    assert studied["card"]["id"] == "minted-greedy-basic"
    # unstarted, and a row per template whether or not it was ever recalled
    assert studied["run"] is None
    assert [one["last_at"] for one in studied["recall"]] == [None]


def test_an_unknown_card_is_not_found(client):
    response = client.get("/api/cards/nope")

    assert (response.status_code, response.json()) == (404, {"detail": "no card nope"})


def test_a_candidate_carries_no_statement(client):
    """Opening the problem serves the statement, so the list stays a list of
    picks."""
    rows = client.get("/api/techniques/sorting/candidates").json()

    assert [row["problem_id"] for row in rows] == ["p-greedy", "p-sorting"]
    assert "statement" not in str(rows)


def test_a_retired_problem_is_not_a_candidate(client, database):
    ProblemStore(database).retire("p-greedy", RetirementReason.DEFECTIVE)

    rows = client.get("/api/techniques/sorting/candidates").json()

    assert [row["problem_id"] for row in rows] == ["p-sorting"]


def test_the_candidates_count_the_user_s_own_attempts_alone(client, database):
    attempted(database, "a1")
    attempted(database, "a2", user_id="u-b71e03")

    rows = client.get("/api/techniques/greedy/candidates").json()

    assert [row["attempt_count"] for row in rows] == [1]


def test_every_problem_is_listed_with_the_techniques_it_carries(client):
    """The page filters by tag, so a listed problem names its techniques."""
    rows = client.get("/api/problems").json()

    assert [(row["problem_id"], row["techniques"]) for row in rows] == [
        ("p-greedy", ["greedy", "sorting"]),
        ("p-sorting", ["sorting"]),
    ]
    assert "statement" not in str(rows)


def test_a_retired_problem_is_not_listed(client, database):
    ProblemStore(database).retire("p-greedy", RetirementReason.DEFECTIVE)

    rows = client.get("/api/problems").json()

    assert [row["problem_id"] for row in rows] == ["p-sorting"]


def test_the_listing_counts_the_user_s_own_attempts_alone(client, database):
    attempted(database, "a1")
    attempted(database, "a2", user_id="u-b71e03")

    rows = {row["problem_id"]: row["attempt_count"] for row in client.get("/api/problems").json()}

    assert rows == {"p-greedy": 1, "p-sorting": 0}


def test_the_listing_offers_the_stalest_problem_first(client, database):
    """One ordering serves both listings: a technique's candidates are a
    filter over every problem."""
    attempted(database, "a1", problem_id="p-greedy")

    rows = client.get("/api/problems").json()

    assert [row["problem_id"] for row in rows] == ["p-sorting", "p-greedy"]


def test_a_picked_problem_is_read_by_its_id_alone(client):
    """A rung of a card's ladder reaches the same problem, so no technique
    names the path."""
    picked = client.get("/api/problems/p-greedy").json()

    assert (picked["title"], picked["techniques"]) == ("p-greedy", ["greedy", "sorting"])
    assert "statement" not in picked


def test_a_picked_problem_counts_the_user_s_own_attempts_alone(client, database):
    attempted(database, "a1")
    attempted(database, "a2", user_id="u-b71e03")
    attempted(database, "a3", problem_id="p-sorting")

    picked = client.get("/api/problems/p-greedy").json()

    assert (picked["attempt_count"], picked["solved_count"]) == (1, 1)


def test_an_unknown_problem_is_not_found(client):
    response = client.get("/api/problems/nope")

    assert (response.status_code, response.json()) == (404, {"detail": "no problem nope"})


def test_a_retired_problem_is_read_at_its_own_url(client, database):
    """The listing names no retired problem, and a link kept from before the
    retirement opens the page the user's attempts sit on."""
    ProblemStore(database).retire("p-greedy", RetirementReason.DEFECTIVE)

    picked = client.get("/api/problems/p-greedy")

    assert picked.status_code == 200
    assert picked.json()["retired"] is True


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


def test_serving_a_retired_problem_is_refused(client, database):
    ProblemStore(database).retire("p-sorting", RetirementReason.DEFECTIVE)

    assert client.post("/api/problems/p-sorting/sittings").status_code == 409


def test_a_served_sitting_is_read_back_by_its_id(client):
    """A reload of the sitting's page reaches the same statement and clock."""
    served = client.post("/api/problems/p-sorting/sittings").json()
    again = client.get(f"/api/sittings/{served['sitting']['id']}").json()

    # no clock runs until the user starts it, and the reload touched the
    # sitting, so its last activity moved
    assert again.pop("elapsed_sec") is served.pop("elapsed_sec") is None
    assert again["sitting"].pop("last_active_at") >= served["sitting"].pop("last_active_at")
    assert again == served


def test_another_user_s_sitting_is_not_found(client, database):
    sitting_id = client.post("/api/problems/p-sorting/sittings").json()["sitting"]["id"]
    other = browsing(database, "u-b71e03")

    assert other.get(f"/api/sittings/{sitting_id}").status_code == 404
