"""Running a form the user typed from memory against the template's cases.

The runner a submission uses, at the same cap: a recall executes code a user
wrote, and nothing about it is safer than a submission.
"""

import ast
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta

from algo_coach import mint
from algo_coach.log import RecallLog, latest_recalls
from algo_coach.runner import CaseRun, agrees, as_json, run, runner
from algo_coach.schema import (
    LADDER,
    Card,
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


def drawn(card: Card, recalled: Iterable[RecallAttempt]) -> Template | None:
    """The template the trainer asks for: never recalled first, then least
    recently recalled. `None` where no template of this card carries cases."""
    latest = latest_recalls(recalled)
    offered = [one for one in card.templates if one.cases]
    if not offered:
        return None
    return min(offered, key=lambda one: _staleness(latest.get(one.id)))


def signature(template: Template) -> str:
    """The line the cases call, which the trainer gives the user to type
    against. `corpus.md`: the parameter order has to be stated somewhere."""
    for node in ast.parse(template.code).body:
        if isinstance(node, ast.FunctionDef) and node.name == "solve":
            returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            return f"def solve({ast.unparse(node.args)}){returns}:"
    raise Missing(f"template {template.slug} defines no `solve` for a recall to answer")


def reveal(template: Template, hint: Hint) -> str:
    """What one hint gives. Each answers more of the question than the last."""
    if hint is Hint.NOTES:
        return template.notes or "This form carries no notes."
    return template.code


def _staleness(one: RecallAttempt | None) -> tuple[int, datetime]:
    # never recalled sorts ahead of every reproduction, whatever its moment
    return (1, one.created_at) if one else (0, datetime.min.replace(tzinfo=UTC))
