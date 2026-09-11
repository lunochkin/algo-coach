"""One timed session on one problem: what the drill loop serves, judges and
mints. `log.md` gives what the record holds and why a pause is an interval."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from algo_coach import mint
from algo_coach.cases import CaseLog
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.problems import ProblemStore
from algo_coach.runner import RUNNER, CaseRun, judge
from algo_coach.schema import (
    Attempt,
    AttemptClaim,
    AttemptVerification,
    CaseOutcome,
    CaseResult,
    ClaimSource,
    Confidence,
    Execution,
    Pause,
    Sitting,
    TestCase,
)

# the cap a sitting judges a submission under. The speedup search picks the
# separating size against it, and generation's own cap sits well above it
DRILL_CAP_MS = 2_000


class Refused(ValueError):
    """A request the sitting's or the problem's state does not allow."""


class Missing(Refused):
    """A record the request names that the user cannot reach."""


class Served(BaseModel):
    """What a solver is handed: the statement and the clock, and nothing the
    problem was written from."""

    model_config = ConfigDict(frozen=True)

    title: str
    statement: str  # the prose, without the signature it ends on
    signature: str | None  # the `def solve(...)` line; none where a statement ends on prose
    sitting: Sitting


class Failure(BaseModel):
    """The first case a submission failed, shown whole: `flows.md`."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    outcome: CaseOutcome
    args: list[Any]
    expected: Any
    returned: Any  # on a wrong answer alone: a crash and a timeout return nothing
    error: str | None  # on a crash alone


class Submitted(BaseModel):
    """The attempt a submission minted, and the per-case verdict behind its
    `solved`."""

    model_config = ConfigDict(frozen=True)

    attempt: Attempt
    verification: AttemptVerification
    failure: Failure | None  # none on a submission that passed every case


def serve(
    problems: ProblemStore,
    sittings: SittingStore,
    problem_id: str,
    *,
    user_id: str,
) -> Served:
    problem = problems.get(problem_id)
    if problem is None:
        raise Missing(f"no problem {problem_id}")
    if not problem.served:
        raise Refused(f"problem {problem_id} is {problem.status}")
    # a refresh or a second tab reaches the clock already running, rather than
    # starting a second one on the same problem
    one = sittings.running(user_id, problem_id)
    if one is None:
        one = mint.sitting(user_id, problem_id)
        sittings.put(one)
    return _served(problem.title, problem.statement, one)


def get(
    problems: ProblemStore,
    sittings: SittingStore,
    sitting_id: str,
    *,
    user_id: str,
) -> Served:
    """What `serve` returned for one of the user's sittings, ended or not. A
    reload of the sitting's page starts no clock."""
    one = _owned(sittings, sitting_id, user_id)
    # the problem as stored, retired or not: the sitting was served before
    problem = problems.get(one.problem_id)
    if problem is None:
        raise ValueError(f"sitting {sitting_id} names no stored problem {one.problem_id}")
    return _served(problem.title, problem.statement, one)


def submit(
    sittings: SittingStore,
    cases: CaseLog,
    log: AttemptLog,
    sitting_id: str,
    code: str,
    *,
    user_id: str,
    now: datetime | None = None,
) -> Submitted:
    # taken before the run: judging takes seconds the solver did not spend
    at = now or _clock()
    one = _running(sittings, sitting_id, user_id)
    if one.paused:
        raise Refused(f"sitting {sitting_id} is paused")
    problem_cases = cases.for_problem(one.problem_id)
    runs = judge(code, problem_cases, cap_ms=DRILL_CAP_MS)
    judged = Execution(cap_ms=DRILL_CAP_MS, runner=RUNNER, results=[result for result, _ in runs])
    attempt = mint.attempt(one, code, solved=judged.verified, finished_at=at)
    verification = mint.attempt_verification(attempt.id, judged)
    log.append_attempt(attempt)
    log.append_verification(verification)
    return Submitted(
        attempt=attempt,
        verification=verification,
        failure=_first_failure(problem_cases, runs),
    )


def claim(
    log: AttemptLog,
    attempt_id: str,
    techniques: Sequence[str],
    *,
    candidates: Sequence[str],
    user_id: str,
    confidence: Confidence,
    declined: bool = False,
) -> AttemptClaim:
    """The user's answer to which of the problem's techniques the attempt
    used. `candidates` is the problem's derived view, which the caller loads
    from the solution logs this call never opens."""
    owned_attempt(log, attempt_id, user_id=user_id)
    outside = [code for code in techniques if code not in candidates]
    if outside:
        raise Refused(f"not among the problem's techniques: {', '.join(outside)}")
    try:
        written = mint.user_claim(
            attempt_id, list(techniques), confidence=confidence, declined=declined
        )
    except ValidationError as error:
        # the request's fault rather than the engine's: a claim naming nothing
        raise Refused("; ".join(one["msg"] for one in error.errors())) from error
    log.append_claim(written)
    return written


def owned_attempt(log: AttemptLog, attempt_id: str, *, user_id: str) -> Attempt:
    # another user's attempt reads as missing, as a sitting does
    found = next((one for one in log.attempts() if one.id == attempt_id), None)
    if found is None or found.user_id != user_id:
        raise Missing(f"no attempt {attempt_id}")
    return found


def unclaimed(log: AttemptLog, sitting_id: str, *, user_id: str) -> list[Attempt]:
    """The sitting's attempts the user has not claimed, in the order they were
    submitted. A machine claim answers no question the loop asked."""
    answered = {one.attempt_id for one in log.claims() if one.source is ClaimSource.USER}
    return [
        one
        for one in log.attempts()
        if one.sitting_id == sitting_id and one.user_id == user_id and one.id not in answered
    ]


def pause(
    store: SittingStore, sitting_id: str, *, user_id: str, now: datetime | None = None
) -> Sitting:
    one = _running(store, sitting_id, user_id)
    if one.paused:
        raise Refused(f"sitting {sitting_id} is already paused")
    return _stored(store, one, pauses=[*one.pauses, Pause(at=now or _clock())])


def resume(
    store: SittingStore, sitting_id: str, *, user_id: str, now: datetime | None = None
) -> Sitting:
    one = _running(store, sitting_id, user_id)
    if not one.paused:
        raise Refused(f"sitting {sitting_id} is not paused")
    return _stored(store, one, pauses=_closed(one.pauses, now or _clock()))


def end(
    store: SittingStore, sitting_id: str, *, user_id: str, now: datetime | None = None
) -> Sitting:
    one = _running(store, sitting_id, user_id)
    at = now or _clock()
    # a pause the user never resumed covers the time away, and closing it here
    # is what leaves the sitting ended with none open
    return _stored(
        store, one, pauses=_closed(one.pauses, at) if one.paused else one.pauses, ended_at=at
    )


def _served(title: str, statement: str, one: Sitting) -> Served:
    prose, signature = _signed(statement)
    return Served(title=title, statement=prose, signature=signature, sitting=one)


def _signed(statement: str) -> tuple[str, str | None]:
    """The prose before the `def solve(...)` line a statement ends on, and that
    line. Split here so no renderer reads a parameter name as markup."""
    text = statement.rstrip()
    # a generated statement ends on the line bare, or inside a fenced block
    fenced = text.endswith("```")
    body = text.removesuffix("```").rstrip()
    start = body.rfind("def solve(")
    at_line_start = start == 0 or (start > 0 and body[start - 1] == "\n")
    if start == -1 or not at_line_start or "\n" in body[start:]:
        return statement, None
    prose = body[:start].rstrip()
    if fenced:
        prose = prose[: prose.rfind("```")].rstrip()
    return prose, body[start:]


def _owned(store: SittingStore, sitting_id: str, user_id: str) -> Sitting:
    one = store.get(sitting_id)
    # another user's sitting reads as missing, so an id reveals nothing
    if one is None or one.user_id != user_id:
        raise Missing(f"no sitting {sitting_id}")
    return one


def _running(store: SittingStore, sitting_id: str, user_id: str) -> Sitting:
    one = _owned(store, sitting_id, user_id)
    if one.ended_at is not None:
        raise Refused(f"sitting {sitting_id} has ended")
    return one


def _first_failure(cases: list[TestCase], runs: list[tuple[CaseResult, CaseRun]]) -> Failure | None:
    for one, (result, ran) in zip(cases, runs, strict=True):
        if result.outcome is not CaseOutcome.PASSED:
            return Failure(
                case_id=one.id,
                outcome=result.outcome,
                args=one.args,
                expected=one.expected,
                returned=ran.value if ran.returned else None,
                error=result.error,
            )
    return None


def _closed(pauses: list[Pause], at: datetime) -> list[Pause]:
    return [*pauses[:-1], Pause(at=pauses[-1].at, until=at)]


def _stored(store: SittingStore, one: Sitting, **changes: object) -> Sitting:
    # revalidated rather than copied: `model_copy` would write a record the
    # interval rules never read
    revised = Sitting.model_validate(one.model_dump() | changes)
    store.put(revised)
    return revised


def _clock() -> datetime:
    return datetime.now(UTC)
