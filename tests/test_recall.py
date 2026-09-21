import pytest
from pydantic import ValidationError

from algo_coach.mint import recall_attempt
from algo_coach.schema import CaseOutcome, CaseResult, Execution, Hint, RecallAttempt

USER = "u-4f9c2a"
FORM = "def solve(xs, target):\n    return 0\n"


def ran(*outcomes: CaseOutcome) -> Execution:
    return Execution(
        cap_ms=2_000,
        runner="local/cpython-3.14",
        results=[
            CaseResult(case_id=f"c{index}", outcome=one, elapsed_ms=1)
            for index, one in enumerate(outcomes)
        ],
    )


def test_a_recall_is_keyed_to_a_card_and_a_template():
    """It answers no problem and submits no solution, so no field keys it to
    an attempt."""
    recall = recall_attempt(
        USER, "c-1", "t-1", code=FORM, hints=[], execution=ran(CaseOutcome.PASSED)
    )

    assert (recall.user_id, recall.card_id, recall.template_id) == (USER, "c-1", "t-1")
    assert "attempt_id" not in RecallAttempt.model_fields


def test_a_recall_carries_what_the_user_typed():
    """The trainer runs the file rather than comparing it with the stored
    form, and the file is what a later reader has."""
    recall = recall_attempt(
        USER, "c-1", "t-1", code=FORM, hints=[], execution=ran(CaseOutcome.PASSED)
    )

    assert recall.code == FORM


def test_the_cases_decide_the_recall():
    """The run is folded to its severest case, as every other run is."""
    recall = recall_attempt(
        USER,
        "c-1",
        "t-1",
        code=FORM,
        hints=[],
        execution=ran(CaseOutcome.PASSED, CaseOutcome.WRONG),
    )

    assert recall.outcome is CaseOutcome.WRONG
    assert not recall.verified


def test_a_hinted_pass_is_not_a_cold_one():
    """`log.md`: which hints were taken before succeeding is part of the
    record, or a decaying form scores the same as a fluent one."""
    hinted = recall_attempt(
        USER,
        "c-1",
        "t-1",
        code=FORM,
        hints=[Hint.NOTES],
        execution=ran(CaseOutcome.PASSED),
    )
    cold = recall_attempt(
        USER, "c-1", "t-1", code=FORM, hints=[], execution=ran(CaseOutcome.PASSED)
    )

    assert hinted.verified and not hinted.cold
    assert cold.cold


def test_a_hint_out_of_order_is_refused():
    """The trainer names the next hint, so a later one is reached through the
    earlier."""
    with pytest.raises(ValidationError, match="in order"):
        recall_attempt(
            USER, "c-1", "t-1", code=FORM, hints=[Hint.FORM], execution=ran(CaseOutcome.PASSED)
        )


def test_a_hint_taken_twice_is_refused():
    with pytest.raises(ValidationError, match="in order"):
        recall_attempt(
            USER,
            "c-1",
            "t-1",
            code=FORM,
            hints=[Hint.NOTES, Hint.NOTES],
            execution=ran(CaseOutcome.PASSED),
        )


def test_a_blank_file_is_a_recall_that_ran():
    """Typing nothing and running is evidence about the memory, and the cases
    answer it as they answer any other file."""
    recall = recall_attempt(
        USER, "c-1", "t-1", code="", hints=[], execution=ran(CaseOutcome.CRASHED)
    )

    assert recall.code == ""
    assert recall.outcome is CaseOutcome.CRASHED
