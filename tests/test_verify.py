from helpers import WRITTEN

from algo_coach.mint import case
from algo_coach.runner import verify
from algo_coach.schema import CaseOutcome

DOUBLE = "def solve(n):\n    return n * 2\n"


def cases(*pairs):
    return [case("p1", args, expected, written=WRITTEN) for args, expected in pairs]


def test_a_case_the_solution_answered_correctly_passed():
    results = verify(DOUBLE, cases(([1], 2), ([3], 6)), cap_ms=3000)

    assert [each.outcome for each in results] == [CaseOutcome.PASSED, CaseOutcome.PASSED]


def test_a_computed_answer_that_differs_is_wrong():
    """Different from a case that yielded nothing: this one was computed and
    is merely incorrect."""
    results = verify(DOUBLE, cases(([1], 2), ([3], 7)), cap_ms=3000)

    assert [each.outcome for each in results] == [CaseOutcome.PASSED, CaseOutcome.WRONG]


def test_a_result_names_the_case_it_decided():
    """A share cannot say which input timed out, so every verdict is keyed to
    the case that produced it."""
    set_ = cases(([1], 2), ([3], 7))

    assert [each.case_id for each in verify(DOUBLE, set_, cap_ms=3000)] == [one.id for one in set_]


def test_a_case_is_decided_by_json_equality():
    """A tuple and a list are one answer under that rule, where `True` and `1`
    are two."""
    tuple_ = "def solve():\n    return (1, 2)\n"
    one = "def solve():\n    return 1\n"

    assert verify(tuple_, cases(([], [1, 2])), cap_ms=3000)[0].outcome is CaseOutcome.PASSED
    assert verify(one, cases(([], True)), cap_ms=3000)[0].outcome is CaseOutcome.WRONG


def test_a_case_that_yielded_no_value_is_that_outcome():
    """Nothing was computed to compare, whatever the case expected."""
    crashing = "def solve():\n    raise ValueError('no')\n"
    slow = "def solve():\n    while True:\n        pass\n"

    assert verify(crashing, cases(([], 1)), cap_ms=3000)[0].outcome is CaseOutcome.CRASHED
    assert verify(slow, cases(([], 1)), cap_ms=200)[0].outcome is CaseOutcome.TIMEOUT


def test_a_verdict_carries_what_the_child_measured():
    """The speedup search reads those numbers, so a result holding only the
    outcome would make every search re-run the whole set."""
    code = "import time\n\n\ndef solve():\n    time.sleep(0.3)\n    return 1\n"

    assert 250 <= verify(code, cases(([], 1)), cap_ms=3000)[0].elapsed_ms < 600


def test_every_case_is_decided_by_default():
    """The canonical stores a count, and a count needs every case decided."""
    code = "def solve(n):\n    if n == 2:\n        raise ValueError('no')\n    return n\n"

    results = verify(code, cases(([1], 1), ([2], 2), ([3], 3)), cap_ms=3000)

    assert [each.outcome for each in results] == [
        CaseOutcome.PASSED,
        CaseOutcome.CRASHED,
        CaseOutcome.PASSED,
    ]


def test_stop_early_stops_at_the_first_case_that_yielded_nothing():
    """What the mutation loop wants: one case that killed the mutant is the
    answer, and the rest cost time to decide."""
    code = "def solve(n):\n    if n == 2:\n        raise ValueError('no')\n    return n\n"

    results = verify(code, cases(([1], 1), ([2], 2), ([3], 3)), cap_ms=3000, stop_early=True)

    assert [each.outcome for each in results] == [CaseOutcome.PASSED, CaseOutcome.CRASHED]


def test_stop_early_never_stops_at_a_wrong_answer():
    """The stop is below the comparison, so a wrong answer is invisible to
    it."""
    results = verify(DOUBLE, cases(([1], 9), ([2], 9), ([3], 6)), cap_ms=3000, stop_early=True)

    assert [each.outcome for each in results] == [
        CaseOutcome.WRONG,
        CaseOutcome.WRONG,
        CaseOutcome.PASSED,
    ]


def test_a_solution_defining_no_solve_fails_every_case():
    results = verify("def other():\n    return 1\n", cases(([1], 1), ([2], 2)), cap_ms=3000)

    assert [each.outcome for each in results] == [CaseOutcome.CRASHED, CaseOutcome.CRASHED]


def test_an_empty_set_decides_nothing():
    """A verification folds to nothing rather than to passed, and this is what
    it folds over."""
    assert verify(DOUBLE, [], cap_ms=3000) == []
