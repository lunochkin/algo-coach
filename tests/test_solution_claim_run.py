import pytest
from helpers import (
    CONFIGURATION,
    PROVENANCE,
    FakeTransport,
    Verdict,
    attempt,
    make_problem,
    own,
    stored_problem,
)

from algo_coach.attempt_claims import ask as claim_one
from algo_coach.calls import CallLog
from algo_coach.classifier import request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import solution as mint_solution
from algo_coach.schema import ClaimSource, SolutionRole
from algo_coach.solution_claims import SolutionClaimLog, candidates, read, read_one
from algo_coach.solutions import SolutionLog
from algo_coach.techniques import codes

answering = FakeTransport.answering

CODE = "def solve(xs):\n    return sorted(xs)[0]\n"
# What the problem carries, and so what its attempts are read against. The
# solution claim is offered the vocabulary instead.
CANDIDATES = ["greedy", "sorting"]


def canonical(code: str = CODE):
    return mint_solution(
        problem_id="p1",
        code=code,
        role=SolutionRole.CANONICAL,
        provenance=PROVENANCE,
    )


@pytest.fixture
def log(database) -> SolutionClaimLog:
    return SolutionClaimLog(database)


def run(client, log, *, code=CODE):
    one = stored(log.root, canonical(code))
    return read(client, log, CallLog(log.root), one, configuration=CONFIGURATION)


def stored(root, one):
    """The canonical in the store, with its problem, since the claim's foreign
    key names the solution."""
    stored_problem(root, "p1")
    SolutionLog(root).append(one)
    return one


def test_a_verdict_is_written_as_a_classifier_reading(log):
    client = answering(Verdict(["sorting"]))

    named = run(client, log)

    (claim,) = log.claims()
    assert named == ["sorting"]
    assert claim.techniques == ["sorting"]
    assert claim.source is ClaimSource.CLASSIFIER


def test_the_reading_is_keyed_to_the_solution(log):
    """A form is displayed by code and so is a technique, so the subject is
    the solution rather than the problem it answers."""
    client = answering(Verdict(["sorting"]))
    one = stored(log.root, canonical())

    read(client, log, CallLog(log.root), one, configuration=CONFIGURATION)

    (claim,) = log.claims()
    assert claim.solution_id == one.id


def test_the_configuration_is_copied_from_the_call(log):
    """The claim log reads without opening the call log, and the copy cannot
    drift: the call is append-only and the copy is made in the same write."""
    client = answering(Verdict(["sorting"]))
    client.cost = 0.0004

    run(client, log)

    (claim,) = log.claims()
    (call,) = own(CallLog(log.root).all())
    assert (claim.model, claim.effort, claim.pin) == (
        CONFIGURATION.model,
        CONFIGURATION.effort,
        CONFIGURATION.pin,
    )
    assert claim.temperature == CONFIGURATION.temperature
    assert (claim.call_id, claim.prompt_hash) == (call.id, call.prompt_hash)
    assert (claim.provider, claim.cost) == ("fake", 0.0004)


def test_an_empty_verdict_is_stored(log):
    """Nothing falls back for a solution — a problem's techniques are folded
    from these claims — so naming none of the vocabulary is this reader's
    answer, and unstored it would be paid for again."""
    client = answering(Verdict([]))

    named = run(client, log)

    (claim,) = log.claims()
    assert named == []
    assert claim.techniques == []


def test_the_candidates_are_the_whole_vocabulary(log):
    """Never the problem's own techniques. Those are folded from claims like
    this one, so a claim constrained by them would answer with what it was
    asked to establish."""
    client = answering(Verdict(["sorting"]))

    run(client, log)

    offered = client.calls[0]["schema"]["properties"]["techniques"]["items"]["enum"]
    assert set(offered) == codes()
    assert offered == candidates()


def test_the_candidate_order_is_fixed(log):
    """The order reaches the prompt, so the prompt hash is taken over it. Drawn
    from a frozenset it would move with the hash seed, and every stored claim
    would read as stale on the next process."""
    assert candidates() == sorted(codes())


def test_one_reader_asks_both_and_the_candidates_are_what_differ(log, database):
    """One rulebook: the system text and the rendering of a criterion are the
    same, so a disagreement between the two records is about the code. What
    separates them is the candidate set, which is why the prompt hashes
    differ."""
    client = answering(Verdict(["sorting"]), Verdict(["sorting"]))
    attempts = AttemptLog(database)
    attempts.append_attempt(attempt("a1", "p1", code=CODE))
    problem = make_problem("p1", techniques=CANDIDATES)

    run(client, log)
    claim_one(
        client,
        attempts,
        CallLog(database),
        attempts.attempts()[0],
        problem,
        configuration=CONFIGURATION,
    )

    (on_solution,) = log.claims()
    (on_attempt,) = attempts.claims()
    assert on_solution.prompt_hash == request_hash(candidates(), CODE)
    assert on_attempt.prompt_hash == request_hash(CANDIDATES, CODE)
    assert on_solution.prompt_hash != on_attempt.prompt_hash
    assert client.asked("system") == {client.calls[0]["system"]}


def test_the_two_records_land_apart(log, database):
    """A claim is product data about code the engine wrote; a claim is the
    user's private testimony. Neither store holds the other's record."""
    client = answering(Verdict(["sorting"]), Verdict(["greedy"]))
    attempts = AttemptLog(database)
    attempts.append_attempt(attempt("a1", "p1", code=CODE))

    run(client, log)
    claim_one(
        client,
        attempts,
        CallLog(database),
        attempts.attempts()[0],
        make_problem("p1", techniques=CANDIDATES),
        configuration=CONFIGURATION,
    )

    assert [one.techniques for one in log.claims()] == [["sorting"]]
    assert [one.techniques for one in attempts.claims()] == [["greedy"]]


def test_a_reading_makes_the_call_and_writes_nothing(log):
    """`read_one` is what a run with several calls in flight uses: the record
    is the caller's, so the log keeps one writer."""
    client = answering(Verdict(["sorting"]))

    named, call = read_one(client, CallLog(log.root), canonical(), configuration=CONFIGURATION)

    assert named == ["sorting"]
    assert call is not None
    assert log.claims() == []
