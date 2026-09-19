import pytest
from helpers import browsing
from matching import card, seeded, template

from algo_coach.log import RecallLog
from algo_coach.sitting import RUNS_PER_MINUTE

USER = "u-4f9c2a"
TECHNIQUE = "sliding-window"
LOWER = "def solve(xs, target):\n    return xs.index(target)\n"
CASES = [{"args": [[1, 2, 3], 2], "expected": 1}, {"args": [[5, 6], 6], "expected": 1}]
PROMPT = "/api/cards/sliding-window/recall"


def recalls(client) -> str:
    """The route the trainer posts to, keyed by the id the prompt drew."""
    return f"{PROMPT}/{client.get(PROMPT).json()['template_id']}"


@pytest.fixture
def client(database):
    seeded(
        database,
        card(
            templates=[
                template("longest-valid-window", code=LOWER, cases=CASES),
                template("fixed-window"),  # no case, so no recall to check
            ]
        ),
    )
    return browsing(database, USER)


def test_a_reproduction_runs_against_the_template_s_cases(client, database):
    """The trainer runs the file rather than comparing it with the stored
    form, so the cases are the whole verdict."""
    recall = client.post(recalls(client), json={"code": LOWER, "hints": []}).json()

    assert [one["outcome"] for one in recall["results"]] == ["passed", "passed"]
    assert recall["cap_ms"] == 2_000
    (stored,) = RecallLog(database).all(USER)
    assert stored.id == recall["id"] and stored.verified


def test_a_wrong_reproduction_is_recorded_as_it_ran(client, database):
    """A recall that failed is evidence about the memory, so it is stored like
    any other."""
    recall = client.post(recalls(client), json={"code": "def solve(xs, t):\n    return 0\n"}).json()

    assert [one["outcome"] for one in recall["results"]] == ["wrong", "wrong"]
    assert not RecallLog(database).all(USER)[0].verified


def test_a_file_that_defines_no_solve_crashes_every_case(client):
    """A blank file is a recall that ran, and the cases answer it as they
    answer any other."""
    recall = client.post(recalls(client), json={"code": ""}).json()

    assert [one["outcome"] for one in recall["results"]] == ["crashed", "crashed"]


def test_the_hints_taken_are_part_of_the_record(client, database):
    """`log.md`: which hints were taken before succeeding is what keeps a
    decaying form from scoring like a fluent one."""
    recall = client.post(recalls(client), json={"code": LOWER, "hints": ["title"]}).json()

    assert recall["hints"] == ["title"]
    assert not RecallLog(database).all(USER)[0].cold


def test_a_hint_out_of_order_is_refused(client):
    response = client.post(recalls(client), json={"code": LOWER, "hints": ["form"]})

    assert response.status_code == 409
    assert "in order" in response.json()["detail"]


def test_a_template_with_no_case_is_never_drawn(client):
    """`content.md`: such a template is read on the card, since nothing can
    check a reproduction of it."""
    drawn = client.get(PROMPT).json()
    fixed = [
        one
        for one in client.get("/api/cards/sliding-window").json()["card"]["templates"]
        if one["slug"] == "fixed-window"
    ]

    assert drawn["template_id"] != fixed[0]["id"]


def test_recalling_a_template_with_no_case_is_refused(client):
    fixed = [
        one
        for one in client.get("/api/cards/sliding-window").json()["card"]["templates"]
        if one["slug"] == "fixed-window"
    ][0]

    response = client.post(f"{PROMPT}/{fixed['id']}", json={"code": LOWER})

    assert response.status_code == 404
    assert "no case" in response.json()["detail"]


def test_an_unknown_template_is_not_found(client):
    response = client.post(f"{PROMPT}/nope", json={"code": LOWER})

    assert (response.status_code, response.json()) == (404, {"detail": "no template nope"})


def test_an_unknown_card_is_not_found(client):
    response = client.post("/api/cards/nope/recall/any", json={"code": LOWER})

    assert (response.status_code, response.json()) == (404, {"detail": "no card nope"})


def test_a_user_s_recalls_are_capped_per_minute(client, database):
    """A recall runs untrusted code on the server, and the broker admits one
    run at a time, so one user's burst is every other user's wait."""
    for _ in range(RUNS_PER_MINUTE):
        assert client.post(recalls(client), json={"code": LOWER}).status_code == 200

    refused = client.post(recalls(client), json={"code": LOWER})

    assert refused.status_code == 429
    assert len(RecallLog(database).all(USER)) == RUNS_PER_MINUTE


def test_the_cap_counts_the_user_s_own_recalls_alone(client, database):
    """Another user's minute is their own, as another user's submissions are."""
    for _ in range(RUNS_PER_MINUTE):
        client.post(recalls(client), json={"code": LOWER})

    theirs = browsing(database, "u-b71e03")
    other = theirs.post(recalls(theirs), json={"code": LOWER})

    assert other.status_code == 200


def test_the_prompt_withholds_the_title_and_the_form(client):
    """Mapping the trigger to the form is the recall being measured, and a
    payload carrying the title answers half of it."""
    prompt = client.get(PROMPT).json()

    assert prompt["trigger"] == "the cue for longest-valid-window"
    assert prompt["signature"] == "def solve(xs, target):"
    assert "longest" not in str(prompt.get("title", "")) and "title" not in prompt
    assert LOWER not in str(prompt)


def test_a_hint_is_given_one_at_a_time(client):
    """The page holds nothing it was not given, so each hint is its own
    request."""
    template_id = client.get(PROMPT).json()["template_id"]

    given = {
        hint: client.get(f"{PROMPT}/{template_id}/hints/{hint}").json()
        for hint in ("title", "notes", "form")
    }

    assert given["title"]["text"] == "longest-valid-window"
    assert given["form"]["text"] == LOWER


def test_the_draw_takes_the_template_never_recalled(client, database):
    """Never recalled first, then least recently recalled."""
    seeded(
        database,
        card(
            slug="two-forms",
            templates=[
                template("first", code=LOWER, cases=CASES),
                template("second", code=LOWER, cases=CASES),
            ],
        ),
    )
    first = client.get("/api/cards/two-forms/recall").json()["template_id"]
    client.post(f"/api/cards/two-forms/recall/{first}", json={"code": LOWER})

    again = client.get("/api/cards/two-forms/recall").json()["template_id"]

    assert again != first
