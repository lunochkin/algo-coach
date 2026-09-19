import pytest
from helpers import browsing, seed_problem
from matching import card, seeded, template

from algo_coach.log import CardRunLog

USER = "u-4f9c2a"
TECHNIQUE = "sliding-window"


@pytest.fixture
def client(database):
    # a ladder of two over three problems, so one is left outside it to probe
    seeded(
        database,
        card(
            templates=[template("longest-valid-window"), template("fixed-window")],
            selector={"technique": TECHNIQUE, "size": 2},
        ),
    )
    for id in ("p-1", "p-2", "p-3"):
        seed_problem(database, id=id, techniques=[TECHNIQUE])
    return browsing(database, USER)


def test_starting_a_card_mints_the_run_and_its_probes(client, database):
    """The ladder is measured from the start, so the run reaches the store
    carrying what the start drew."""
    run = client.post("/api/cards/sliding-window/runs").json()

    assert (run["user_id"], run["started_at"]) == (USER, run["probes"][0]["assigned_at"])
    (stored,) = CardRunLog(database).all(USER)
    assert stored.id == run["id"]
    assert [one.problem_id for one in stored.probes] == [run["probes"][0]["problem_id"]]


def test_a_probe_is_never_a_rung(client):
    """The ladder teaches the form, and a probe tests whether the form is
    recognised unprompted. The ladder of two takes p-1 and p-2, so the probe is
    what it left."""
    run = client.post("/api/cards/sliding-window/runs").json()

    assert [one["problem_id"] for one in run["probes"]] == ["p-3"]


def test_starting_a_started_card_returns_the_run_it_has(client, database):
    """A second run on one card is deferred, so the start reaches the open run
    rather than minting another."""
    first = client.post("/api/cards/sliding-window/runs").json()

    again = client.post("/api/cards/sliding-window/runs").json()

    assert again["id"] == first["id"]
    assert len(CardRunLog(database).all(USER)) == 1


def test_starting_an_unknown_card_is_not_found(client):
    response = client.post("/api/cards/nope/runs")

    assert (response.status_code, response.json()) == (404, {"detail": "no card nope"})


def test_a_run_belongs_to_the_user_who_started_it(client, database):
    """Every private record keys to its user, and another user's start is
    another run."""
    client.post("/api/cards/sliding-window/runs")
    other = browsing(database, "u-b71e03")

    other.post("/api/cards/sliding-window/runs")

    assert len(CardRunLog(database).all(USER)) == 1
    assert len(CardRunLog(database).all("u-b71e03")) == 1


def test_a_card_whose_ladder_holds_the_corpus_offers_no_probe(database):
    """A probe is never drawn from the ladder, so a corpus the ladder exhausts
    leaves a run with none rather than reusing a rung."""
    seeded(
        database,
        card(
            templates=[template("longest-valid-window")],
            selector={"technique": TECHNIQUE, "size": 5},
        ),
    )
    for id in ("p-1", "p-2"):
        seed_problem(database, id=id, techniques=[TECHNIQUE])

    run = browsing(database, USER).post("/api/cards/sliding-window/runs").json()

    assert run["probes"] == []
