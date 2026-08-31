"""What the two runs decide about a drafted problem: which gate rejects it,
and what a surviving one carries."""

import json

from algo_coach.generation import Discard, check, checks
from algo_coach.generation.generator import DraftCase
from algo_coach.schema import CaseOutcome

DOUBLE = "def solve(x):\n    return x * 2\n"
# the same function reached another way, which is what a blind reference is
TWICE = "def solve(x):\n    return x + x\n"
CAP_MS = 1000


def cases(*pairs) -> list[DraftCase]:
    """Cases as the generation call wrote them: the arguments, and the value
    it declared `solve` returns. Both arrive as JSON text."""
    return [DraftCase(args=json.dumps(list(args)), expected=json.dumps(one)) for args, one in pairs]


def checked(*pairs, canonical: str = DOUBLE, reference: str = TWICE, cap_ms: int = CAP_MS):
    return check(cases(*pairs), canonical=canonical, reference=reference, cap_ms=cap_ms)


def test_a_problem_both_solutions_answer_the_same_way_survives():
    """The prose has one reading, and the canonical returns what its own call
    declared."""
    result = checked(([2], 4), ([5], 10))

    assert result.survived
    assert result.outcome is CaseOutcome.PASSED
    assert [one.args for one in result.cases] == [[2], [5]]


def test_a_landing_case_carries_the_reference_s_answer():
    """A case the canonical produced passes by construction, so the stored
    value is the one the independent solution computed."""
    result = checked(([2], 4))

    assert [one.expected for one in result.cases] == [4]


def test_a_canonical_yielding_no_value_discards_the_problem():
    """Nothing establishes what the case returns, so there is no problem to
    keep."""
    result = checked(([2], 4), canonical="def solve(x):\n    raise ValueError(x)\n")

    assert not result.survived
    assert result.discard is Discard.NO_VALUE
    assert result.outcome is CaseOutcome.CRASHED
    assert result.cases == []


def test_a_canonical_contradicting_its_own_cases_discards_the_problem():
    """One call wrote the code and the cases, so a disagreement between them
    means it wrote one of the two wrong."""
    result = checked(([2], 4), ([5], 11))

    assert result.discard is Discard.MISDECLARED
    assert result.outcome is CaseOutcome.WRONG
    assert [one.returned for one in result.misdeclarations] == [10]
    assert result.cases == []


def test_the_reference_is_never_run_where_the_canonical_failed(monkeypatch):
    """The two solutions are compared to test the statement, and a call that
    contradicted itself leaves nothing to test."""

    def unreachable(*args, **kwargs):
        raise AssertionError("the reference was run")

    monkeypatch.setattr(checks, "outputs", unreachable)

    assert checked(([2], 5)).discard is Discard.MISDECLARED
    assert checked(([2], 4), canonical="def other():\n    return 1\n").discard is Discard.NO_VALUE


def test_two_solutions_that_disagree_discard_the_problem():
    """The prose admits two readings, which is the statement's fault rather
    than either solution's."""
    result = checked(([2], 4), ([5], 10), reference="def solve(x):\n    return x * 3\n")

    assert result.discard is Discard.DISAGREED
    assert [one.args for one in result.disagreements] == [[2], [5]]
    assert result.cases == []


def test_a_canonical_that_passed_its_own_cases_can_still_be_discarded():
    """The gates are ordered, and the run's outcome is a fact about the
    canonical rather than about whether the problem was kept."""
    result = checked(([2], 4), reference="def solve(x):\n    return x * 3\n")

    assert result.outcome is CaseOutcome.PASSED
    assert not result.survived


def test_a_case_beyond_the_reference_is_held_apart_rather_than_discarded():
    """The ordinary path past the reference's reach. Taking the canonical's
    answer there is the step after this one, so the case is neither settled
    nor lost."""
    slow = "def solve(x):\n    import time\n\n    time.sleep(9 if x > 5 else 0)\n    return x + x\n"

    result = checked(([2], 4), ([9], 18), reference=slow, cap_ms=300)

    assert result.survived
    assert [one.args for one in result.cases] == [[2]]
    assert [one.args for one in result.beyond] == [[9]]


def test_a_reference_that_computed_no_case_discards_the_problem():
    """Every expected output would be the canonical's own, and `verified`
    would then mean only that the solution agrees with itself."""
    result = checked(([2], 4), reference="def solve(x):\n    raise ValueError(x)\n")

    assert result.discard is Discard.UNTESTED
    assert result.outcome is CaseOutcome.PASSED
    assert result.cases == []
