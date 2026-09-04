"""One configuration's pass over the eval set: plan the calls, fold the
answers."""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import Configuration
from algo_coach.claims.run import ABORT_AFTER, Failed, store
from algo_coach.claims.sample import recency
from algo_coach.claims.stale import readings_at
from algo_coach.classifier import DEFAULT, request_hash
from algo_coach.log import AttemptLog
from algo_coach.schema import Attempt, Call, Problem, TechniqueClaim


class ReadResult(BaseModel):
    verdicts: dict[str, list[str]] = Field(default_factory=dict)  # attempt id -> techniques
    read: int = 0  # attempts this run paid a call for
    reused: int = 0  # answered from a stored reading
    undecided: int = 0  # named no candidate: stored, and never scored
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False
    # A reading stored before the price was recorded carries none and is left
    # out of both, so the mean is over what is known.
    cost: float = 0.0
    costed: int = 0
    # Ids, not the token counts: a claim carries none, and a report joins them
    # from the call log.
    call_ids: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    """One configuration's share of a run. Selecting is separated from asking
    so one consumer drives several of them, appending on its own thread."""

    configuration: Configuration
    asking: list[Attempt] = Field(default_factory=list)  # newest first, after `limit`
    result: ReadResult = Field(default_factory=ReadResult)
    answered: int = 0  # of `asking`, however the answer went
    consecutive: int = 0  # failures since the last answer


def select(
    attempts: Sequence[Attempt],
    problems: Mapping[str, Problem],
    *,
    claims: Sequence[TechniqueClaim],
    configuration: Configuration = DEFAULT,
    limit: int | None = None,
    fresh: bool = False,
) -> Plan:
    """What one classifier still has to pay for, and what the log already
    answers.

    `limit` caps the calls, not the attempts — a stored reading is free, so a
    capped run adds to what earlier runs read. Makes no call and writes
    nothing.
    """
    asked = {
        attempt.id: request_hash(problems[attempt.problem_id].techniques, attempt.code or "")
        for attempt in attempts
        if attempt.problem_id in problems
    }
    stored = {} if fresh else readings_at(claims, configuration, asked)
    plan = Plan(configuration=configuration)

    unread: list[Attempt] = []
    for attempt in attempts:
        reading = stored.get(attempt.id)
        if reading is None:
            unread.append(attempt)
            continue
        if not reading.techniques:
            # A stored decline is a verdict, not a missing answer.
            plan.result.verdicts[attempt.id] = []
            plan.result.undecided += 1
        plan.result.verdicts[attempt.id] = reading.techniques
        plan.result.reused += 1
        # Its own price, from the run that paid it, never a rate applied now.
        if reading.cost is not None:
            plan.result.cost += reading.cost
            plan.result.costed += 1
        if reading.call_id is not None:
            plan.result.call_ids.append(reading.call_id)

    plan.asking = sorted(unread, key=recency, reverse=True)[:limit]
    return plan


def absorb(
    log: AttemptLog,
    plan: Plan,
    attempt: Attempt,
    answer: tuple[list[str], Call | None] | None,
    failure: Exception | None,
) -> dict[str, Any]:
    """Fold one answer into the plan that asked for it, returning what to
    report.

    Writes on the calling thread, the one consumer however many calls are in
    flight. A run of failures ends this plan alone; the others keep reading.
    """
    plan.answered += 1
    techniques, call = answer if answer is not None else ([], None)

    if failure is not None:
        # Broad on purpose: a refusal or a dropped connection is one attempt's
        # problem, and a run must not lose the ones behind it.
        plan.result.failed.append(Failed(attempt_id=attempt.id, reason=repr(failure)))
        plan.consecutive += 1
        if plan.consecutive == ABORT_AFTER:
            plan.result.aborted = True
        return {"reason": repr(failure)}

    # Answered, so the classifier is reachable: an undecided verdict is a
    # reading, not a failure.
    plan.consecutive = 0
    if call is not None:
        plan.result.call_ids.append(call.id)
        if call.cost is not None:
            plan.result.cost += call.cost
            plan.result.costed += 1
    if call is not None:
        # Stored whether or not it named anything, so no later run at this
        # configuration pays for the question again.
        store(log, attempt.id, techniques, call)
    if not techniques:
        plan.result.verdicts[attempt.id] = []
        plan.result.undecided += 1
        return {}
    plan.result.verdicts[attempt.id] = techniques
    plan.result.read += 1
    return {"techniques": techniques}
