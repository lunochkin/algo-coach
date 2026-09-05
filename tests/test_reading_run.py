import pytest
from helpers import CONFIGURATION, FakeTransport, Verdict, attempt, make_problem

from algo_coach.calls import CallLog
from algo_coach.claims import ask as claim_one
from algo_coach.classifier import request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import solution as mint_solution
from algo_coach.readings import ReadingLog, candidates, read, read_one
from algo_coach.schema import MachineProvenance, ReadingSource, SolutionRole
from algo_coach.techniques import codes

answering = FakeTransport.answering

CODE = "def solve(xs):\n    return sorted(xs)[0]\n"
# What the problem carries, and so what its attempts are read against. The
# solution reading is offered the vocabulary instead.
CANDIDATES = ["greedy", "sorting"]


def canonical(code: str = CODE):
    return mint_solution(
        problem_id="p1",
        code=code,
        role=SolutionRole.CANONICAL,
        written=MachineProvenance(
            model="a-model", effort="medium", pin="a/pin", prompt_hash="deadbeef", call_id="call-0"
        ),
    )


@pytest.fixture
def log(tmp_path) -> ReadingLog:
    return ReadingLog(tmp_path)


def run(client, log, *, code=CODE):
    return read(client, log, CallLog(log.root), canonical(code), configuration=CONFIGURATION)


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

    read(client, log, CallLog(log.root), one, configuration=CONFIGURATION)

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


def test_the_candidates_are_the_whole_vocabulary(log):
    """Never the problem's own techniques. Those are folded from readings like
    this one, so a reading constrained by them would answer with what it was
    asked to establish."""
    client = answering(Verdict(["sorting"]))

    run(client, log)

    offered = client.calls[0]["schema"]["properties"]["techniques"]["items"]["enum"]
    assert set(offered) == codes()
    assert offered == candidates()


def test_the_candidate_order_is_fixed(log):
    """The order reaches the prompt and the prompt is what the digest is taken
    over. Drawn from a frozenset it would move with the hash seed, and every
    stored reading would read as stale on the next process."""
    assert candidates() == sorted(codes())


def test_one_reader_asks_both_and_the_candidates_are_what_differ(log, tmp_path):
    """One rulebook: the system text and the rendering of a criterion are the
    same, so a disagreement between the two records is about the code. What
    separates them is the candidate set, which is why the digests differ."""
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
    assert reading.prompt_hash == request_hash(candidates(), CODE)
    assert claim.prompt_hash == request_hash(CANDIDATES, CODE)
    assert reading.prompt_hash != claim.prompt_hash
    assert client.asked("system") == {client.calls[0]["system"]}


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

    named, call = read_one(client, CallLog(log.root), canonical(), configuration=CONFIGURATION)

    assert named == ["sorting"]
    assert call is not None
    assert log.readings() == []
