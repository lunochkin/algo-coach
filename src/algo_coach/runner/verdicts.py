"""What a run decided, case by case. Comparison sits here, never in the
backend."""

from collections.abc import Sequence

from algo_coach.runner.encoding import agrees
from algo_coach.runner.execution import CaseRun, RunOutcome, run
from algo_coach.schema import CaseOutcome, CaseResult, Json, TestCase

DECIDED = {RunOutcome.TIMEOUT: CaseOutcome.TIMEOUT, RunOutcome.CRASHED: CaseOutcome.CRASHED}


def verify(
    code: str,
    cases: Sequence[TestCase],
    *,
    cap_ms: int,
    stop_early: bool = False,
) -> list[CaseResult]:
    return [one for one, _ in judge(code, cases, cap_ms=cap_ms, stop_early=stop_early)]


def judge(
    code: str,
    cases: Sequence[TestCase],
    *,
    cap_ms: int,
    stop_early: bool = False,
) -> list[tuple[CaseResult, CaseRun]]:
    """Each case's result beside the run it was decided from, which holds the
    returned value a result does not store."""
    # `run` rather than `outputs`: a `CaseResult` carries the elapsed time,
    # and `stop_early` is why the zip is not strict
    ran = run(
        code,
        [case.args for case in cases],
        cap_ms=cap_ms,
        repeats=[case.repeats for case in cases],
        stop_early=stop_early,
    )
    return [(result(case, one), one) for case, one in zip(cases, ran, strict=False)]


def result(case: TestCase, ran: CaseRun) -> CaseResult:
    return CaseResult(
        case_id=case.id, outcome=decide(ran, case.expected), elapsed_ms=ran.elapsed_ms
    )


def decide(ran: CaseRun, expected: Json) -> CaseOutcome:
    # apart from `result` because generation decides the canonical before any
    # case has an id
    if not ran.returned:
        return DECIDED[ran.outcome]
    return CaseOutcome.PASSED if agrees(ran.value, expected) else CaseOutcome.WRONG
