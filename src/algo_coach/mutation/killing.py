"""What the case set does to a mutant: kills it, or leaves it standing.

A survivor is a mistake no case catches, so it names a case that has to exist.
Nothing is stored: the verdicts are re-derived with the mutants.
"""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from algo_coach.mutation.mutants import Mutant
from algo_coach.runner import decide, run
from algo_coach.schema import CaseOutcome

# how many times the loop asks for cases before it stops. `corpus.md` gives
# the reason; a round that kills nothing stops it earlier
ROUNDS = 2


class Case(Protocol):
    """A case on either side of landing: a `SettledCase` before, a `TestCase`
    after."""

    args: list[Any]
    expected: Any


@dataclass(frozen=True)
class Verdict:
    """One mutant against the case set, and the first case that failed it.
    Both are absent on a survivor, which no case failed."""

    mutant: Mutant
    case: int | None = None
    outcome: CaseOutcome | None = None

    @property
    def survived(self) -> bool:
        return self.outcome is None


def kill(mutants: Sequence[Mutant], cases: Sequence[Case], *, cap_ms: int) -> list[Verdict]:
    """A verdict per mutant, in the order they were enumerated."""
    return [_against(one, cases, cap_ms=cap_ms) for one in mutants]


def survivors(verdicts: Iterable[Verdict]) -> list[Verdict]:
    """The mutants the set left standing. Each names a case that has to exist."""
    return [one for one in verdicts if one.survived]


def _against(mutant: Mutant, cases: Sequence[Case], *, cap_ms: int) -> Verdict:
    # `stop_early`: a crash or a timeout kills where it happens, and a wrong
    # answer is decided up here, so the run cannot stop at one
    ran = run(mutant.code, [case.args for case in cases], cap_ms=cap_ms, stop_early=True)
    for index, (case, one) in enumerate(zip(cases, ran, strict=False)):
        outcome = decide(one, case.expected)
        if outcome is not CaseOutcome.PASSED:
            return Verdict(mutant, case=index, outcome=outcome)
    return Verdict(mutant)


__all__ = ["ROUNDS", "Case", "Verdict", "kill", "survivors"]
