"""What each case produced, as a value where there was one."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from algo_coach.runner.execution import CaseRun, RunOutcome, run


@dataclass(frozen=True)
class NoValue:
    # its own type rather than the bare outcome: `RunOutcome` is a `StrEnum`,
    # so a solution returning "timeout" must not read as one that timed out
    outcome: RunOutcome


def outputs(
    code: str,
    args: Sequence[Sequence[Any]],
    *,
    cap_ms: int,
    stop_early: bool = False,
) -> list[Any]:
    # the elapsed time is dropped: the speedup search reads it from `run`
    return [answered(each) for each in run(code, args, cap_ms=cap_ms, stop_early=stop_early)]


def answered(ran: CaseRun) -> Any:
    return ran.value if ran.returned else NoValue(ran.outcome)
