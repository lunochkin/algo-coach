"""Running a form the user typed from memory against the template's cases.

The runner a submission uses, at the same cap: a recall executes code a user
wrote, and nothing about it is safer than a submission.
"""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from algo_coach import mint
from algo_coach.log import RecallLog
from algo_coach.runner import CaseRun, agrees, as_json, run, runner
from algo_coach.schema import (
    LADDER,
    CaseOutcome,
    CaseResult,
    Execution,
    Hint,
    Json,
    RecallAttempt,
    Template,
    TemplateCase,
)
from algo_coach.sitting import DRILL_CAP_MS, RUNS_PER_MINUTE, Missing, Refused, TooOften

DECIDED = {"timeout": CaseOutcome.TIMEOUT, "crashed": CaseOutcome.CRASHED}


def reproduce(
    log: RecallLog,
    card_id: str,
    template: Template,
    code: str,
    hints: Sequence[Hint],
    *,
    user_id: str,
    now: datetime | None = None,
) -> RecallAttempt:
    """One reproduction: run what was typed, and record how it went."""
    at = now or datetime.now(UTC)
    if not template.cases:
        raise Missing(f"template {template.slug} carries no case to check a recall against")
    # the record refuses it too; refused here, so the trainer reads a verdict
    # rather than a defect
    if tuple(hints) != LADDER[: len(hints)]:
        raise Refused(f"the hints are taken in order: {', '.join(LADDER)}")
    # before the run: a recall past the cap starts no container, as a
    # submission past it does not
    if len(log.all(user_id, since=at - timedelta(minutes=1))) >= RUNS_PER_MINUTE:
        raise TooOften(f"{RUNS_PER_MINUTE} recalls a minute is the cap")
    record = mint.recall_attempt(
        user_id,
        card_id,
        template.id,
        code=code,
        hints=hints,
        execution=judged(template, code),
    )
    log.append(record)
    return record


def judged(template: Template, code: str) -> Execution:
    """What the template's cases made of the file, case by case."""
    ran = run(code, [case.args for case in template.cases], cap_ms=DRILL_CAP_MS)
    return Execution(
        cap_ms=DRILL_CAP_MS,
        runner=runner(),
        results=[
            CaseResult(
                # the case's position, since a template's cases are rewritten
                # whole by a re-seed and carry no key of their own
                case_id=str(position),
                outcome=outcome(one, case, unordered=template.unordered),
                elapsed_ms=one.elapsed_ms,
                error=one.error,
            )
            for position, (case, one) in enumerate(zip(template.cases, ran, strict=False))
        ],
    )


def outcome(ran: CaseRun, case: TemplateCase, *, unordered: bool) -> CaseOutcome:
    if not ran.returned:
        return DECIDED[ran.outcome]
    if agrees(settled(ran.value, unordered), settled(case.expected, unordered)):
        return CaseOutcome.PASSED
    return CaseOutcome.WRONG


def settled(value: Json, unordered: bool) -> Json:
    """A set answer's top level sorted, so the order two correct reproductions
    emit it in is not a difference. `content.md` gives why the sort stops
    there."""
    if not unordered or not isinstance(value, list):
        return value
    return sorted(value, key=as_json)
