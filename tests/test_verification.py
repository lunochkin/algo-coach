"""One run of a solution against a problem's cases.

Its own record because the outcome is a fact about the run rather than about
the code. The cap and the machine decide a timeout, and a crash can come from
the runner, so the same solution run twice can differ.
"""

import pytest
from pydantic import ValidationError

from algo_coach.mint import verification
from algo_coach.schema import CaseOutcome, CaseResult, Verification


def result(case_id: str, outcome: str, **overrides) -> CaseResult:
    """A case that yielded a value was timed, so the helper carries one."""
    timed = {"elapsed_ms": 1} if outcome in (CaseOutcome.PASSED, CaseOutcome.WRONG) else {}
    return CaseResult(**{"case_id": case_id, "outcome": outcome} | timed | overrides)


def run(**overrides) -> Verification:
    return verification(**{"solution_id": "s1", "timeout_ms": 2000} | overrides)


def test_a_run_is_keyed_to_what_it_ran():
    assert run().solution_id == "s1"


def test_a_run_naming_no_solution_is_rejected():
    with pytest.raises(ValidationError, match="solution_id"):
        run(solution_id="")


def test_a_run_stores_the_cap_that_decided_a_timeout():
    """Two runs under different caps are not comparable, and the outcome is
    the only thing that would show it."""
    assert run(timeout_ms=500).timeout_ms == 500


def test_a_cap_of_nothing_is_rejected():
    """Every case would time out, so the run would decide nothing about the
    solution."""
    with pytest.raises(ValidationError, match="timeout_ms"):
        run(timeout_ms=0)


def test_a_result_is_per_case_and_says_how_it_went():
    """A share cannot say which input timed out, and the set of cases that
    passed cannot say why the rest did not."""
    one = run(results=[result("c1", "passed"), result("c2", "timeout")])

    assert [(each.case_id, each.outcome) for each in one.results] == [
        ("c1", CaseOutcome.PASSED),
        ("c2", CaseOutcome.TIMEOUT),
    ]


def test_the_outcomes_are_the_four_a_failure_mode_reads_apart():
    """Only one of the three failures is evidence of slowness, so a bare
    pass-or-fail would collapse the distinction a diagnosis needs."""
    assert set(CaseOutcome) == {
        CaseOutcome.PASSED,
        CaseOutcome.WRONG,
        CaseOutcome.TIMEOUT,
        CaseOutcome.CRASHED,
    }


def test_an_unnamed_outcome_is_rejected():
    with pytest.raises(ValidationError, match="outcome"):
        result("c1", "exploded")


def test_a_result_naming_no_case_is_rejected():
    """It has no meaning apart from the case it reports on."""
    with pytest.raises(ValidationError, match="case_id"):
        result("", "passed")


def test_a_run_that_decided_nothing_has_no_outcome():
    """An empty set would otherwise fold to passed and claim a verification
    that never happened."""
    assert run().outcome is None
    assert run().verified is False


def test_every_case_passing_is_what_verified_means():
    one = run(results=[result("c1", "passed"), result("c2", "passed")])

    assert one.outcome is CaseOutcome.PASSED
    assert one.verified is True


@pytest.mark.parametrize("outcome", [CaseOutcome.WRONG, CaseOutcome.TIMEOUT, CaseOutcome.CRASHED])
def test_one_failing_case_decides_the_run(outcome):
    one = run(results=[result("c1", "passed"), result("c2", outcome)])

    assert one.outcome is outcome
    assert one.verified is False


def test_the_most_severe_failure_stands():
    """A solution that only ran slowly is otherwise correct, which is a
    different remedy from one returning a wrong answer."""
    worst = run(results=[result("c1", "timeout"), result("c2", "wrong"), result("c3", "crashed")])

    assert worst.outcome is CaseOutcome.CRASHED

    slow_and_wrong = run(results=[result("c1", "timeout"), result("c2", "wrong")])

    assert slow_and_wrong.outcome is CaseOutcome.WRONG


def test_a_timeout_is_a_fact_about_the_run_read_at_one_case():
    """It surfaces where the large input is, and the level it is read at does
    not change what it means."""
    one = run(results=[result("c1", "passed"), result("c2", "timeout")])

    assert one.outcome is CaseOutcome.TIMEOUT
    assert [each.case_id for each in one.results if each.outcome is CaseOutcome.TIMEOUT] == ["c2"]


def test_the_overall_outcome_is_not_stored():
    """Aggregates are derived views. A stored copy would disagree with the
    results the moment a case was answered."""
    assert "outcome" not in Verification.model_fields
    assert "verified" not in Verification.model_fields


def test_a_run_is_minted_an_id_and_stamped():
    """Re-running is legal, so two runs of one solution have to be told
    apart."""
    assert run().id != run().id
    assert run().created_at.tzinfo is not None


def test_a_result_carries_what_the_child_measured():
    """The speedup search reads those numbers. A result holding only the
    outcome would make every later search re-run the whole set."""
    timed = CaseResult(case_id="c1", outcome="passed", elapsed_ms=17)

    assert timed.elapsed_ms == 17


def test_a_case_that_yielded_a_value_carries_its_time():
    """`PASSED` and `WRONG` come from a child that ran `solve` to completion,
    so it measured one."""
    for outcome in (CaseOutcome.PASSED, CaseOutcome.WRONG):
        with pytest.raises(ValidationError, match="elapsed_ms"):
            CaseResult(case_id="c1", outcome=outcome)


def test_a_case_the_child_never_timed_carries_no_number():
    """Code that defines no `solve` never reaches one, and a timeout the
    parent's own timer decided was reported by nothing."""
    assert result("c1", "crashed").elapsed_ms is None
    assert result("c1", "timeout").elapsed_ms is None


def test_a_negative_measurement_is_rejected():
    with pytest.raises(ValidationError, match="elapsed_ms"):
        CaseResult(case_id="c1", outcome="passed", elapsed_ms=-1)
