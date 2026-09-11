import pytest
from helpers import PROVENANCE_FIELDS, stored_solution

from algo_coach.cases import CaseLog
from algo_coach.mint import verification
from algo_coach.schema import CaseOutcome, CaseResult, TestCase
from algo_coach.verifications import VerificationLog


@pytest.fixture(autouse=True)
def referenced(database):
    """The solutions the runs name, and the case each result names."""
    stored_solution(database, "s1")
    stored_solution(database, "s2")
    CaseLog(database).append(
        TestCase(
            id="c1",
            problem_id="p1",
            args=[1],
            expected=1,
            expected_from="reference",
            round=0,
            **PROVENANCE_FIELDS,
        )
    )


def run(solution_id: str = "s1", **overrides):
    fields = {
        "solution_id": solution_id,
        "cap_ms": 2000,
        "runner": "subprocess/cpython-3.14",
    } | overrides
    return verification(**fields)


def test_an_empty_store_reads_as_nothing(database):
    assert VerificationLog(database).verifications() == []
    assert VerificationLog(database).for_solution("s1") == []


def test_a_run_reads_back_whole(database):
    """The per-case results are what a failure mode reads, so they have to
    survive the round trip rather than collapsing to a verdict."""
    store = VerificationLog(database)
    one = run(results=[CaseResult(case_id="c1", outcome="timeout")])
    store.append(one)

    read = store.verifications()

    assert read == [one]
    assert read[0].outcome is CaseOutcome.TIMEOUT


def test_a_second_run_does_not_supersede_the_first(database):
    """Neither answers for the other. A run under a different cap is a
    different question, and both stay readable."""
    store = VerificationLog(database)
    slow = run(cap_ms=100, results=[CaseResult(case_id="c1", outcome="timeout")])
    generous = run(cap_ms=5000, results=[CaseResult(case_id="c1", outcome="passed", elapsed_ms=1)])
    store.append(slow)
    store.append(generous)

    assert store.verifications() == [slow, generous]
    assert [one.cap_ms for one in store.verifications()] == [100, 5000]


def test_runs_are_read_per_solution(database):
    store = VerificationLog(database)
    mine = [run("s1"), run("s1")]
    theirs = run("s2")
    for one in [*mine, theirs]:
        store.append(one)

    assert store.for_solution("s1") == mine
    assert store.for_solution("s2") == [theirs]


def test_a_solution_never_run_reads_as_nothing(database):
    """Distinct from one that ran and failed, which carries a record saying
    so."""
    store = VerificationLog(database)
    store.append(run("s1"))

    assert store.for_solution("s2") == []
