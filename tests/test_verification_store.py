from algo_coach.mint import verification
from algo_coach.schema import CaseOutcome, CaseResult
from algo_coach.verifications import VerificationLog


def run(solution_id: str = "s1", **overrides):
    fields = {
        "solution_id": solution_id,
        "timeout_ms": 2000,
        "runner": "subprocess/cpython-3.14",
    } | overrides
    return verification(**fields)


def test_an_empty_store_reads_as_nothing(tmp_path):
    assert VerificationLog(tmp_path).verifications() == []
    assert VerificationLog(tmp_path).for_solution("s1") == []


def test_a_run_reads_back_whole(tmp_path):
    """The per-case results are what a failure mode reads, so they have to
    survive the round trip rather than collapsing to a verdict."""
    store = VerificationLog(tmp_path)
    one = run(results=[CaseResult(case_id="c1", outcome="timeout")])
    store.append(one)

    read = store.verifications()

    assert read == [one]
    assert read[0].outcome is CaseOutcome.TIMEOUT


def test_a_second_run_does_not_supersede_the_first(tmp_path):
    """Neither answers for the other. A run under a different cap is a
    different question, and both stay readable."""
    store = VerificationLog(tmp_path)
    slow = run(timeout_ms=100, results=[CaseResult(case_id="c1", outcome="timeout")])
    generous = run(
        timeout_ms=5000, results=[CaseResult(case_id="c1", outcome="passed", elapsed_ms=1)]
    )
    store.append(slow)
    store.append(generous)

    assert store.verifications() == [slow, generous]
    assert [one.timeout_ms for one in store.verifications()] == [100, 5000]


def test_runs_are_read_per_solution(tmp_path):
    store = VerificationLog(tmp_path)
    mine = [run("s1"), run("s1")]
    theirs = run("s2")
    for one in [*mine, theirs]:
        store.append(one)

    assert store.for_solution("s1") == mine
    assert store.for_solution("s2") == [theirs]


def test_a_solution_never_run_reads_as_nothing(tmp_path):
    """Distinct from one that ran and failed, which carries a record saying
    so."""
    store = VerificationLog(tmp_path)
    store.append(run("s1"))

    assert store.for_solution("s2") == []
