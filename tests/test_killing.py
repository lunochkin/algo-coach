"""What the cases do to the mutants: a kill on a wrong answer, a crash or a
timeout, and the survivors the next call is asked about."""

from dataclasses import dataclass
from typing import Any

from algo_coach.mutation import Mutant, Operator, kill, mutants, survivors
from algo_coach.schema import CaseOutcome

CAP_MS = 1000
DOUBLE = "def solve(x):\n    return x * 2\n"


@dataclass(frozen=True)
class Case:
    args: list[Any]
    expected: Any


def cases(*pairs) -> list[Case]:
    return [Case(args=list(args), expected=one) for args, one in pairs]


def mutant(code: str) -> Mutant:
    """A mutant by hand, where the test is about the run rather than the walk."""
    return Mutant(code=code, operator=Operator.CONSTANT, change="1 → 2", line=1)


def test_a_wrong_answer_kills():
    """The ordinary kill: the case separates the mutant from the canonical."""
    [verdict] = kill([mutant("def solve(x):\n    return x * 3\n")], cases(([2], 4)), cap_ms=CAP_MS)

    assert not verdict.survived
    assert verdict.outcome is CaseOutcome.WRONG
    assert verdict.case == 0


def test_a_crash_kills():
    """A mutant that raises demonstrates nothing, and the case still caught the
    change."""
    [verdict] = kill([mutant("def solve(x):\n    return x[0]\n")], cases(([2], 4)), cap_ms=CAP_MS)

    assert verdict.outcome is CaseOutcome.CRASHED


def test_a_timeout_kills():
    """A change that stops the loop terminating is caught by the cap rather
    than by an answer."""
    forever = "def solve(x):\n    while x > 0:\n        x += 1\n    return x\n"

    [verdict] = kill([mutant(forever)], cases(([2], 4)), cap_ms=300)

    assert verdict.outcome is CaseOutcome.TIMEOUT


def test_a_mutant_no_case_separates_survives():
    """`x >= 0` answers every case `x > 0` does, so nothing here catches it."""
    standing = "def solve(x):\n    return x if x >= 1 else 0\n"

    [verdict] = kill([mutant(standing)], cases(([2], 2), ([5], 5)), cap_ms=CAP_MS)

    assert verdict.survived
    assert verdict.case is None
    assert verdict.outcome is None


def test_the_verdict_names_the_first_case_that_failed():
    """A survivor is reported at the input that has to be in the set, so which
    case failed is part of the verdict."""
    off_by_one = "def solve(x):\n    return x * 2 if x else 1\n"

    [verdict] = kill([mutant(off_by_one)], cases(([2], 4), ([0], 0)), cap_ms=CAP_MS)

    assert verdict.case == 1
    assert verdict.outcome is CaseOutcome.WRONG


def test_a_verdict_per_mutant_in_the_order_enumerated():
    """The report pairs with the set, so a survivor is found by its own
    change."""
    verdicts = kill(mutants(DOUBLE), cases(([2], 4)), cap_ms=CAP_MS)

    assert [one.mutant for one in verdicts] == mutants(DOUBLE)
    assert [one.change for one in mutants(DOUBLE)] == ["2 → 3", "2 → 1", "* → //"]


def test_a_case_set_that_kills_everything_leaves_no_survivor():
    """What a set is measured on: nothing left for a call to answer."""
    verdicts = kill(mutants(DOUBLE), cases(([2], 4), ([5], 10)), cap_ms=CAP_MS)

    assert survivors(verdicts) == []


def test_survivors_are_the_mutants_left_standing():
    """One case at 2 answers every change but the direction of the test."""
    threshold = "def solve(x):\n    return x >= 1\n"

    verdicts = kill(mutants(threshold), cases(([2], True)), cap_ms=CAP_MS)

    assert [one.mutant.change for one in survivors(verdicts)] == ["1 → 2", "1 → 0", ">= → >"]


def test_an_empty_case_set_kills_nothing():
    """No case ran, so no change was caught."""
    verdicts = kill(mutants(DOUBLE), [], cap_ms=CAP_MS)

    assert survivors(verdicts) == verdicts
