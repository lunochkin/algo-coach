"""What each case produced, as a value where there was one.

Generation compares two solutions before any `expected` exists, so what it
needs from a run is answers rather than verdicts. A case that yielded nothing
is still reported, since which cases those are is read by the solution's role:
a canonical that crashed discards the problem, where a reference that did so
is the ordinary path beyond its reach.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from algo_coach.runner.execution import RunOutcome, run


@dataclass(frozen=True)
class NoValue:
    """A case the solution answered with nothing, and how.

    Its own type rather than the outcome alone. `RunOutcome` is a `StrEnum`,
    so a solution returning `"timeout"` would be indistinguishable from one
    that ran past the cap. No solution can return this, because a value
    arrives decoded from JSON.
    """

    outcome: RunOutcome


def outputs(
    code: str,
    args: Sequence[Sequence[Any]],
    *,
    cap_ms: int,
    stop_early: bool = False,
) -> list[Any]:
    """One entry per case: the value it returned, or a `NoValue` saying why
    there is none.

    Shorter than the set under `stop_early`, as `run` is. The elapsed time is
    dropped here: the speedup search reads it from `run`, where comparing two
    solutions does not.
    """
    return [
        each.value if each.returned else NoValue(each.outcome)
        for each in run(code, args, cap_ms=cap_ms, stop_early=stop_early)
    ]
