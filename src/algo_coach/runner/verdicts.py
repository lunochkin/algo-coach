"""What a run decided, case by case.

Comparison sits here rather than in the backend. The executor is handed code,
arguments and a cap, and returns what each call produced, so the rule deciding
a case cannot vary by where the code ran and a sandbox is never told what a
case expects.
"""

from collections.abc import Sequence

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
    """Run `code` against each case, and say how each one went.

    Read from `run` rather than from `outputs`, because a `CaseResult` carries
    what the child measured and `outputs` drops it. A case that yielded a
    value was timed, and the speedup search reads those numbers.

    Shorter than the set under `stop_early`, as the run is. The attempt path
    wants every case decided, where the mutation loop stops at the first one
    that killed the mutant.
    """
    ran = run(code, [case.args for case in cases], cap_ms=cap_ms, stop_early=stop_early)
    return [result(case, one) for case, one in zip(cases, ran, strict=False)]


def result(case: TestCase, ran: CaseRun) -> CaseResult:
    """One case's verdict. A call that yielded no value is that outcome
    whatever the case expected: nothing was computed to compare."""
    if not ran.returned:
        return CaseResult(case_id=case.id, outcome=DECIDED[ran.outcome], elapsed_ms=ran.elapsed_ms)
    passed = agrees(ran.value, case.expected)
    return CaseResult(
        case_id=case.id,
        outcome=CaseOutcome.PASSED if passed else CaseOutcome.WRONG,
        elapsed_ms=ran.elapsed_ms,
    )
