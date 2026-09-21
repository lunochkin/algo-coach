from datetime import datetime, timedelta

import pytest
from helpers import browsing, seed_problem
from matching import card, seeded, template

from algo_coach.log import AttemptLog, CardRunLog, RecallLog
from algo_coach.mint import recall_attempt
from algo_coach.schema import Attempt, CaseOutcome, CaseResult, Execution, Hint


def solved_attempt(problem_id: str, *, at: datetime, id: str) -> Attempt:
    return Attempt(id=id, user_id=USER, problem_id=problem_id, finished_at=at, solved=True)


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


def test_the_card_reads_its_run_the_ladder_and_the_probes(client):
    """The three views a start makes measurable, on the card's own route."""
    started = client.post("/api/cards/sliding-window/runs").json()

    studied = client.get("/api/cards/sliding-window").json()

    assert studied["run"]["id"] == started["id"]
    assert [one["problem"]["id"] for one in studied["rungs"]] == ["p-1", "p-2"]
    # named by the problem, since the page shows what it offers
    assert [(one["problem"]["title"], one["attempted"]) for one in studied["probes"]] == [
        ("p-3", False)
    ]


def test_the_ladder_s_progress_counts_the_run(client, database):
    """A rung is solved by an attempt since the run began, and an attempt from
    before it counts for nothing."""
    # a ladder over the whole corpus, so an attempt reorders no rung off it
    seeded(
        database,
        card(
            slug="windows-wide",
            templates=[template("longest-valid-window")],
            selector={"technique": TECHNIQUE, "size": 3},
        ),
    )
    started = client.post("/api/cards/windows-wide/runs").json()
    began = datetime.fromisoformat(started["started_at"])
    log = AttemptLog(database)
    log.append_attempt(solved_attempt("p-1", at=began - timedelta(days=1), id="a-before"))
    log.append_attempt(solved_attempt("p-2", at=began + timedelta(minutes=5), id="a-after"))

    studied = client.get("/api/cards/windows-wide").json()

    assert {one["problem"]["id"]: one["solved"] for one in studied["rungs"]} == {
        "p-1": False,
        "p-2": True,
        "p-3": False,
    }


def test_a_card_reads_the_recall_state_of_each_template(client, database):
    """The last reproduction per template, and a row for the form never
    recalled."""
    studied = client.get("/api/cards/sliding-window").json()
    first = studied["card"]["templates"][0]["id"]
    RecallLog(database).append(
        recall_attempt(
            USER,
            studied["card"]["id"],
            first,
            code="def solve():\n    return 1\n",
            hints=[Hint.NOTES],
            execution=Execution(
                cap_ms=2_000,
                runner="local/cpython-3.14",
                results=[CaseResult(case_id="c0", outcome=CaseOutcome.PASSED, elapsed_ms=1)],
            ),
        )
    )

    read = client.get("/api/cards/sliding-window").json()["recall"]

    assert [(one["template_id"] == first, one["hints"], one["verified"]) for one in read] == [
        (True, ["notes"], True),
        (False, [], False),
    ]
