import pytest
from helpers import browsing
from matching import card, seeded, template

from algo_coach.log import RecallLog
from algo_coach.sitting import RUNS_PER_MINUTE

USER = "u-4f9c2a"
TECHNIQUE = "sliding-window"
LOWER = "def solve(xs, target):\n    return xs.index(target)\n"
CASES = [{"args": [[1, 2, 3], 2], "expected": 1}, {"args": [[5, 6], 6], "expected": 1}]
RECALLS = "/api/cards/sliding-window/templates/longest-valid-window/recalls"


@pytest.fixture
def client(database):
    seeded(
        database,
        card(
            templates=[
                template("longest-valid-window", cases=CASES),
                template("fixed-window"),  # no case, so no recall to check
            ]
        ),
    )
    return browsing(database, USER)


def test_a_reproduction_runs_against_the_template_s_cases(client, database):
    """The trainer runs the file rather than comparing it with the stored
    form, so the cases are the whole verdict."""
    recall = client.post(RECALLS, json={"code": LOWER, "hints": []}).json()

    assert [one["outcome"] for one in recall["results"]] == ["passed", "passed"]
    assert recall["cap_ms"] == 2_000
    (stored,) = RecallLog(database).all(USER)
    assert stored.id == recall["id"] and stored.verified


def test_a_wrong_reproduction_is_recorded_as_it_ran(client, database):
    """A recall that failed is evidence about the memory, so it is stored like
    any other."""
    recall = client.post(RECALLS, json={"code": "def solve(xs, t):\n    return 0\n"}).json()

    assert [one["outcome"] for one in recall["results"]] == ["wrong", "wrong"]
    assert not RecallLog(database).all(USER)[0].verified


def test_a_file_that_defines_no_solve_crashes_every_case(client):
    """A blank file is a recall that ran, and the cases answer it as they
    answer any other."""
    recall = client.post(RECALLS, json={"code": ""}).json()

    assert [one["outcome"] for one in recall["results"]] == ["crashed", "crashed"]


def test_the_hints_taken_are_part_of_the_record(client, database):
    """`log.md`: which hints were taken before succeeding is what keeps a
    decaying form from scoring like a fluent one."""
    recall = client.post(RECALLS, json={"code": LOWER, "hints": ["title"]}).json()

    assert recall["hints"] == ["title"]
    assert not RecallLog(database).all(USER)[0].cold


def test_a_hint_out_of_order_is_refused(client):
    response = client.post(RECALLS, json={"code": LOWER, "hints": ["form"]})

    assert response.status_code == 409
    assert "in order" in response.json()["detail"]


def test_a_template_with_no_case_is_never_recalled(client):
    """`content.md`: such a template is read on the card, since nothing can
    check a reproduction of it."""
    response = client.post(
        "/api/cards/sliding-window/templates/fixed-window/recalls", json={"code": LOWER}
    )

    assert response.status_code == 404
    assert "no case" in response.json()["detail"]


def test_an_unknown_template_is_not_found(client):
    response = client.post("/api/cards/sliding-window/templates/nope/recalls", json={"code": LOWER})

    assert (response.status_code, response.json()) == (404, {"detail": "no template nope"})


def test_an_unknown_card_is_not_found(client):
    response = client.post("/api/cards/nope/templates/any/recalls", json={"code": LOWER})

    assert (response.status_code, response.json()) == (404, {"detail": "no card nope"})


def test_a_user_s_recalls_are_capped_per_minute(client, database):
    """A recall runs untrusted code on the server, and the broker admits one
    run at a time, so one user's burst is every other user's wait."""
    for _ in range(RUNS_PER_MINUTE):
        assert client.post(RECALLS, json={"code": LOWER}).status_code == 200

    refused = client.post(RECALLS, json={"code": LOWER})

    assert refused.status_code == 429
    assert len(RecallLog(database).all(USER)) == RUNS_PER_MINUTE


def test_the_cap_counts_the_user_s_own_recalls_alone(client, database):
    """Another user's minute is their own, as another user's submissions are."""
    for _ in range(RUNS_PER_MINUTE):
        client.post(RECALLS, json={"code": LOWER})

    other = browsing(database, "u-b71e03").post(RECALLS, json={"code": LOWER})

    assert other.status_code == 200
