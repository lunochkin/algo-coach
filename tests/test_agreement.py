"""What a run of one case set decides: whether the call that wrote the problem
wrote its code and its cases from one reading, whose answer is stored, and when
the statement admits two readings."""

import json

import pytest

from algo_coach.generation import Disagreement, Misdeclaration, misdeclared, settle
from algo_coach.generation.agreement import agrees
from algo_coach.generation.generator import DraftCase
from algo_coach.runner import NoValue, RunOutcome
from algo_coach.schema import ExpectedSource


def cases(*args) -> list[list]:
    """The arguments settling reads. What a case expects is what a run
    establishes, so nothing carries one on the way in."""
    return [list(one) for one in args]


def declared(*pairs) -> list[DraftCase]:
    """Cases as the generation call wrote them, each carrying the value it
    said `solve` returns. Both fields arrive as JSON text."""
    return [DraftCase(args=json.dumps(list(args)), expected=json.dumps(one)) for args, one in pairs]


def test_a_canonical_answering_what_was_declared_reports_nothing():
    """One call wrote the code and the cases, and they agree."""
    assert misdeclared(declared(([1, 2], 3), ([], 0)), [3, 0]) == []


def test_a_misdeclaration_carries_both_answers():
    """Which of the two the call wrote wrong is not the question. It wrote one
    of them wrong, and the pair is what shows it."""
    assert misdeclared(declared(([1], 2)), [9]) == [
        Misdeclaration(args=[1], declared=2, returned=9)
    ]


def test_every_case_is_read():
    """The gate reports what the call declared wrong, and one case says less
    than all of them."""
    reported = misdeclared(declared(([1], 1), ([2], 2), ([3], 3)), [1, 9, 8])

    assert [one.args for one in reported] == [[2], [3]]


def test_the_declared_value_is_compared_as_json():
    """By the rule the runner encodes a return with: a tuple and a list are one
    answer, where a boolean and a number are two."""
    assert misdeclared(declared(([1], [1, 2])), [(1, 2)]) == []
    assert misdeclared(declared(([1], 1)), [True]) != []


def test_a_case_that_yielded_no_value_is_not_a_misdeclaration():
    """Nothing was computed to compare. A canonical yielding nothing is what
    discards the problem a step later."""
    assert misdeclared(declared(([1], 1)), [NoValue(RunOutcome.TIMEOUT)]) == []


def test_a_run_that_answered_a_different_number_of_cases_reports_nothing():
    """A fault in the runner rather than a call that declared wrong."""
    with pytest.raises(ValueError):
        misdeclared(declared(([1], 1), ([2], 2)), [1])


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


def test_a_case_past_the_reference_takes_the_canonical_s_answer():
    """Beyond the largest input the reference finishes, only the canonical can
    compute one. That is its reach rather than a failure, so the case lands."""
    settled = settle(cases([1]), canonical=[3], reference=[NoValue(RunOutcome.TIMEOUT)])

    assert settled.agreed
    assert [one.expected for one in settled.cases] == [3]
    assert [one.expected_from for one in settled.cases] == [ExpectedSource.CANONICAL]


def test_a_stored_case_names_the_solution_that_computed_it():
    """Two cases in a set are not equally strong evidence, and nothing but the
    field says which is which."""
    settled = settle(cases([1], [2]), canonical=[1, 2], reference=[1, NoValue(RunOutcome.CRASHED)])

    assert [one.expected_from for one in settled.cases] == [
        ExpectedSource.REFERENCE,
        ExpectedSource.CANONICAL,
    ]
    assert [one.args for one in settled.tested] == [[1]]
