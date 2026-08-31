"""What a run decided, case by case.

Comparison sits here rather than in the backend. The executor is handed code,
arguments and a cap, and returns what each call produced, so the rule deciding
a case cannot vary by where the code ran and a sandbox is never told what a
case expects.
"""

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
    """One case's verdict, as the record stores it."""
    return CaseResult(
        case_id=case.id, outcome=decide(ran, case.expected), elapsed_ms=ran.elapsed_ms
    )


def decide(ran: CaseRun, expected: Any) -> CaseOutcome:
    """How one call went against the value it was to return.

    Apart from `result` because generation reads it before any case has an id:
    the canonical is decided against the `expected` its own call declared, and
    there is no `TestCase` to key a verdict to yet.

    A call that yielded no value is that outcome whatever was expected:
    nothing was computed to compare.
    """
    if not ran.returned:
        return DECIDED[ran.outcome]
    return CaseOutcome.PASSED if agrees(ran.value, expected) else CaseOutcome.WRONG
