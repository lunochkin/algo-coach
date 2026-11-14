from datetime import UTC, datetime

import pytest
from helpers import browsing
from matching import card, seeded, template

from climb.judgements import ItemStore
from climb.judging import build
from climb.log import JudgementLog

USER = "u-4f9c2a"
FORM = (
    "def solve(xs):\n"
    "    best = xs[0]\n"
    "    for x in xs:\n"
    "        if x > best:\n"
    "            best = x\n"
    "    return best\n"
)
CASES = [
    {"args": [[3, 9, 4]], "expected": 9},
    {"args": [[7]], "expected": 7},
    {"args": [[9, 2]], "expected": 9},
]


@pytest.fixture
def client(database):
    (held,) = seeded(
        database, card(slug="largest", templates=[template("largest", code=FORM, cases=CASES)])
    )
    added, _ = build([held], [], now=datetime(2026, 11, 14, tzinfo=UTC))
    ItemStore(database).add(added)
    return browsing(database, USER)


def test_an_item_is_served_without_its_answer(client):
    """The page sends nothing before the user answers, so the item carries no
    answer the page could show early."""
    served = client.get("/api/judging/next").json()

    assert set(served) == {
        "item_id",
        "card_slug",
        "card_title",
        "depth",
        "template_title",
        "asks",
        "example",
        "lines",
    }
    assert served["example"] == {"args": [[3, 9, 4]], "expected": 9}
    assert served["depth"] == 0
    assert served["lines"][0] == "def solve(xs):"


def test_a_clean_item_called_clean_is_right(client, database):
    clean = next(one for one in ItemStore(database).all() if one.clean)

    decided = client.post(f"/api/judging/{clean.id}", json={"called_clean": True}).json()

    assert decided == {"verdict": "right", "line": None, "correct": None, "case": None}
    assert len(JudgementLog(database).for_user(USER)) == 1


def test_a_flaw_on_its_line_is_located_and_shows_its_case(client, database):
    flawed = next(one for one in ItemStore(database).all() if not one.clean)

    decided = client.post(
        f"/api/judging/{flawed.id}", json={"called_clean": False, "line": flawed.line}
    ).json()

    assert decided["verdict"] == "located"
    assert decided["correct"] == FORM.splitlines()[flawed.line - 1]
    assert decided["case"]["args"] == flawed.case_args
    assert decided["case"]["outcome"] in ("wrong", "crashed")


def test_a_flaw_on_another_line_is_spotted_and_a_clean_call_missed(client, database):
    flawed = next(one for one in ItemStore(database).all() if not one.clean)
    other = 1 if flawed.line != 1 else 2

    spotted = client.post(f"/api/judging/{flawed.id}", json={"called_clean": False, "line": other})
    missed = client.post(f"/api/judging/{flawed.id}", json={"called_clean": True})

    assert (spotted.json()["verdict"], missed.json()["verdict"]) == ("spotted", "missed")


def test_a_flawed_call_needs_a_line(client, database):
    clean = next(one for one in ItemStore(database).all() if one.clean)

    response = client.post(f"/api/judging/{clean.id}", json={"called_clean": False})

    assert response.status_code == 422


def test_the_next_item_is_one_not_yet_answered(client, database):
    first = client.get("/api/judging/next").json()["item_id"]
    client.post(f"/api/judging/{first}", json={"called_clean": True})

    assert client.get("/api/judging/next").json()["item_id"] != first


def test_a_card_narrows_the_items_and_an_unknown_card_is_not_found(client):
    assert client.get("/api/judging/next?card=largest").status_code == 200
    assert client.get("/api/judging/next?card=nope").status_code == 404
