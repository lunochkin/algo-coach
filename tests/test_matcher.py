"""One card's templates against one problem: what is asked, and what a verdict
turns into."""

import json

import pytest
from matching import PROCEDURE, FakeTransport, Verdict, card, problem, seeded, template

from algo_coach.calls import CallLog
from algo_coach.matches import DEFAULT, MatcherError, candidates, match, request_hash


def read(tmp_path, client: FakeTransport, cards=None, techniques=("sliding-window",)):
    (one,) = seeded(tmp_path, *(cards or [card()]))
    return one, match(client, CallLog(tmp_path), one, problem("p1", techniques=list(techniques)))


def test_a_procedure_template_is_no_candidate(tmp_path):
    """A framing procedure is exercised by every problem its technique
    reaches, so a per-problem verdict on one carries no information."""
    (one,) = seeded(
        tmp_path,
        card(templates=[template("framing", **PROCEDURE), template("longest-valid-window")]),
    )

    assert [t.slug for t in candidates(one)] == ["longest-valid-window"]


def test_one_call_carries_every_candidate(tmp_path):
    """Not a call per pair: the candidates are the card's templates and the
    answer is the subset, which is one request rather than six."""
    client = FakeTransport.answering(Verdict(["longest-valid-window"]))

    _, (matched, call) = read(tmp_path, client)

    assert len(client.calls) == 1
    assert matched == ["longest-valid-window"]
    assert call is not None
    sent = client.calls[0]
    assert sent["schema"]["properties"]["templates"]["items"]["enum"] == [
        "longest-valid-window",
        "fixed-window",
    ]


def test_the_statement_is_the_evidence(tmp_path):
    """Which form a problem exercises is a question about what it asks; its
    techniques answer what it is about."""
    client = FakeTransport.answering(Verdict([]))
    (one,) = seeded(tmp_path)
    asked = problem("p1", techniques=["sliding-window"], statement="Find the longest substring ...")

    match(client, CallLog(tmp_path), one, asked)

    content = client.calls[0]["content"]
    assert "Find the longest substring ..." in content
    # The form itself, not only its name: a cue alone would ask the model to
    # match a shape it has to guess.
    assert "def longest_valid_window(): pass" in content
    assert "the cue for longest-valid-window" in content


def test_a_single_candidate_is_still_asked(tmp_path):
    """Unlike a lone technique, where the problem itself answers: here the
    verdict is the record, and yes and no both have to be paid for once."""
    client = FakeTransport.answering(Verdict([]))

    _, (matched, call) = read(tmp_path, client, [card(templates=[template("only-form")])])

    assert (matched, call is not None) == ([], True)


def test_a_card_of_procedures_alone_asks_nothing(tmp_path):
    client = FakeTransport.answering()

    _, (matched, call) = read(
        tmp_path, client, [card(templates=[template("framing", **PROCEDURE)])]
    )

    assert (matched, call, client.calls) == ([], None, [])


def test_a_verdict_outside_the_candidates_is_dropped(tmp_path):
    """The schema's guarantee ends with the request; the record outlives it."""
    client = FakeTransport.answering(Verdict(["longest-valid-window", "invented"]))

    _, (matched, _) = read(tmp_path, client)

    assert matched == ["longest-valid-window"]


def test_no_verdict_is_an_error(tmp_path):
    """A refusal or an answer cut short: the pair stays unread rather than
    landing as a card that matches nothing."""
    with pytest.raises(MatcherError):
        read(tmp_path, FakeTransport.answering(Verdict()))


def test_the_digest_is_per_pair(tmp_path):
    """A template edited on one card re-tests that card's pairs and leaves
    every other one settled."""
    one, edited = seeded(
        tmp_path,
        card(),
        card("sliding-window-advanced", templates=[template("longest-valid-window", code="new")]),
    )
    asked = problem("p1", techniques=["sliding-window"])
    elsewhere = problem("p2", techniques=["sliding-window"], statement="A different question ...")

    assert request_hash(one, asked) == request_hash(one, asked)
    assert request_hash(one, asked) != request_hash(one, elsewhere)
    assert request_hash(edited, asked) != request_hash(one, asked)


def test_the_reading_is_greedy_and_pinned(tmp_path):
    """The configuration is part of what identifies a record, so what a run
    sampled at and which build answered are sent and stored."""
    client = FakeTransport.answering(Verdict([]))

    read(tmp_path, client)

    sent = client.calls[0]
    assert (sent["temperature"], sent["pin"]) == (DEFAULT.temperature, DEFAULT.pin)
    assert DEFAULT.temperature == 0.0


def test_the_call_is_recorded(tmp_path):
    client = FakeTransport.answering(Verdict(["fixed-window"]))

    read(tmp_path, client)

    (call,) = CallLog(tmp_path).all()
    assert json.loads(call.response)["templates"] == ["fixed-window"]
    assert call.provider == "fake"
