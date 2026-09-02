"""What a run decided, case by case. Comparison sits here, never in the backend."""

from collections.abc import Sequence
from typing import Any

from algo_coach.runner.encoding import agrees
from algo_coach.runner.execution import CaseRun, RunOutcome, run
from algo_coach.schema import CaseOutcome, CaseResult, TestCase

DECIDED = {RunOutcome.TIMEOUT: CaseOutcome.TIMEOUT, RunOutcome.CRASHED: CaseOutcome.CRASHED}


def verify(
    code: str,
    cases: Sequence[TestCase],
    *,
    cap_ms: int,
    stop_early: bool = False,
) -> list[CaseResult]:
    # `run` rather than `outputs`: a `CaseResult` carries the elapsed time,
    # and `stop_early` is why the zip is not strict
    ran = run(code, [case.args for case in cases], cap_ms=cap_ms, stop_early=stop_early)
    return [result(case, one) for case, one in zip(cases, ran, strict=False)]


def result(case: TestCase, ran: CaseRun) -> CaseResult:
    return CaseResult(
        case_id=case.id, outcome=decide(ran, case.expected), elapsed_ms=ran.elapsed_ms
    )


def decide(ran: CaseRun, expected: Any) -> CaseOutcome:
    # apart from `result` because generation decides the canonical before any
    # case has an id
    if not ran.returned:
        return DECIDED[ran.outcome]
    return CaseOutcome.PASSED if agrees(ran.value, expected) else CaseOutcome.WRONG
