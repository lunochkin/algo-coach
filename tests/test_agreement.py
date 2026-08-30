"""What two runs of one case set decide: whose answer is stored, and when the
statement admits two readings."""

import pytest

from algo_coach.generation import Disagreement, settle
from algo_coach.generation.agreement import agrees
from algo_coach.generation.generator import DraftCase


def cases(*args) -> list[DraftCase]:
    """Cases as the generation call wrote them, whose JSON arrives as text.
    The model's own expected output is never stored, so these carry none."""
    return [DraftCase(args=list(one), expected="null") for one in args]


def test_the_stored_answer_is_the_reference_s():
    """A case the canonical produced passes by construction, and `verified`
    would then mean only that the solution agrees with itself."""
    settled = settle(cases([1, 2]), canonical=[3], reference=[3])

    assert settled.agreed
    assert [one.expected for one in settled.cases] == [3]


def test_a_disagreement_carries_both_answers():
    """Which of the two is wrong is not the question. The statement admitted
    two readings, and the pair is what shows it."""
    settled = settle(cases([1]), canonical=[2], reference=[3])

    assert not settled.agreed
    assert settled.disagreements == [Disagreement(args=[1], canonical=2, reference=3)]
    assert settled.cases == []


def test_every_case_is_decided():
    """Which inputs the two readings differ on is what a discarded problem is
    reported by, and the first of them says less than all of them."""
    settled = settle(cases([1], [2], [3]), canonical=[1, 9, 3], reference=[1, 8, 4])

    assert [one.args for one in settled.disagreements] == [[2], [3]]
    assert [one.args for one in settled.cases] == [[1]]


def test_a_string_answer_is_stored_as_it_was_returned():
    """A case decodes JSON text on the way in, so a decoded answer must not be
    decoded a second time."""
    settled = settle(cases([1]), canonical=["ab"], reference=["ab"])

    assert settled.cases[0].expected == "ab"


def test_agreement_is_agreement_as_json():
    """That is what a stored case holds: a tuple and a list are one answer
    under that rule, where a boolean and a number are two."""
    assert agrees((1, 2), [1, 2])
    assert not agrees(True, 1)
    assert not agrees(1, 1.0)


def test_a_run_that_answered_a_different_number_of_cases_decides_nothing():
    """A fault in the runner rather than a disagreement between the
    solutions."""
    with pytest.raises(ValueError):
        settle(cases([1], [2]), canonical=[1], reference=[1, 2])
