"""One classifier reads a canonical and an attempt, and the two records land
apart.

Two prompts asking one question would drift, and neither score would compare.
So what these assert is that the reader is the same one — same system text,
same digest for the same code and candidates — while the record written differs
in kind, in store and in who owns it.
"""

import pytest
from helpers import CONFIGURATION, FakeTransport, Verdict, attempt, make_problem

from algo_coach.calls import CallLog
from algo_coach.claims import ask as claim_one
from algo_coach.classifier import request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import solution as mint_solution
from algo_coach.readings import ReadingLog, read, read_one
from algo_coach.schema import ReadingSource, SolutionRole

answering = FakeTransport.answering

CODE = "def solve(xs):\n    return sorted(xs)[0]\n"
CANDIDATES = ["greedy", "sorting"]


def canonical(code: str = CODE):
    return mint_solution(
        problem_id="p1",
        code=code,
        role=SolutionRole.CANONICAL,
        model="a-model",
        effort="medium",
        pin="a/pin",
        prompt_hash="deadbeef",
        call_id="call-0",
    )


@pytest.fixture
def log(tmp_path) -> ReadingLog:
    return ReadingLog(tmp_path)


def run(client, log, *, candidates=CANDIDATES, code=CODE):
    return read(
        client,
        log,
        CallLog(log.root),
        canonical(code),
        candidates,
        configuration=CONFIGURATION,
    )


def test_a_verdict_is_written_as_a_classifier_reading(log):
    client = answering(Verdict(["sorting"]))

    named = run(client, log)

    (reading,) = log.readings()
    assert named == ["sorting"]
    assert reading.techniques == ["sorting"]
    assert reading.source is ReadingSource.CLASSIFIER


def test_the_reading_is_keyed_to_the_solution(log):
    """A form is displayed by code and so is a technique, so the subject is
    the solution rather than the problem it answers."""
    client = answering(Verdict(["sorting"]))
    one = canonical()

    read(client, log, CallLog(log.root), one, CANDIDATES, configuration=CONFIGURATION)

    (reading,) = log.readings()
    assert reading.solution_id == one.id


def test_the_configuration_is_copied_from_the_call(log):
    """The reading log reads without opening the call log, and the copy cannot
    drift: the call is append-only and the copy is made in the same write."""
    client = answering(Verdict(["sorting"]))
    client.cost = 0.0004

    run(client, log)

    (reading,) = log.readings()
    (call,) = CallLog(log.root).all()
    assert (reading.model, reading.effort, reading.pin) == (
        CONFIGURATION.model,
        CONFIGURATION.effort,
        CONFIGURATION.pin,
    )
    assert reading.temperature == CONFIGURATION.temperature
    assert (reading.call_id, reading.prompt_hash) == (call.id, call.prompt_hash)
    assert (reading.provider, reading.cost) == ("fake", 0.0004)


def test_an_empty_verdict_is_stored(log):
    """Nothing falls back for a solution — a problem's techniques are folded
    from these readings — so naming none of the vocabulary is this reader's
    answer, and unstored it would be paid for again."""
    client = answering(Verdict([]))

    named = run(client, log)

    (reading,) = log.readings()
    assert named == []
    assert reading.techniques == []


def test_nothing_is_stored_where_nothing_was_read(log):
    """A reading carries its whole configuration, so a verdict no call
    produced cannot be written down."""
    client = answering()

    named = run(client, log, candidates=["sorting"])

    assert named == ["sorting"]
    assert log.readings() == []
    assert client.calls == []


def test_the_same_question_is_asked_of_an_attempt_and_a_canonical(log, tmp_path):
    """One reader, two records. The digest is what a re-run compares, so the
    same code against the same candidates has to reach the same text — two
    prompts would drift, and neither score would compare."""
    client = answering(Verdict(["sorting"]), Verdict(["sorting"]))
    attempts = AttemptLog(tmp_path)
    attempts.append_attempt(attempt("a1", "p1", code=CODE))
    problem = make_problem("p1", techniques=CANDIDATES)

    run(client, log)
    claim_one(
        client,
        attempts,
        CallLog(tmp_path),
        attempts.attempts()[0],
        problem,
        configuration=CONFIGURATION,
    )

    (reading,) = log.readings()
    (claim,) = attempts.claims()
    assert reading.prompt_hash == claim.prompt_hash == request_hash(CANDIDATES, CODE)
    assert client.asked("content") == {client.calls[0]["content"]}


def test_the_two_records_land_apart(log, tmp_path):
    """A reading is product data about code the engine wrote; a claim is the
    user's private testimony. Neither store holds the other's record."""
    client = answering(Verdict(["sorting"]), Verdict(["greedy"]))
    attempts = AttemptLog(tmp_path)
    attempts.append_attempt(attempt("a1", "p1", code=CODE))

    run(client, log)
    claim_one(
        client,
        attempts,
        CallLog(tmp_path),
        attempts.attempts()[0],
        make_problem("p1", techniques=CANDIDATES),
        configuration=CONFIGURATION,
    )

    assert [one.techniques for one in log.readings()] == [["sorting"]]
    assert [one.techniques for one in attempts.claims()] == [["greedy"]]


def test_a_reading_makes_the_call_and_writes_nothing(log):
    """`read_one` is what a run with several calls in flight uses: the record
    is the caller's, so the log keeps one writer."""
    client = answering(Verdict(["sorting"]))

    named, call = read_one(
        client, CallLog(log.root), canonical(), CANDIDATES, configuration=CONFIGURATION
    )

    assert named == ["sorting"]
    assert call is not None
    assert log.readings() == []
