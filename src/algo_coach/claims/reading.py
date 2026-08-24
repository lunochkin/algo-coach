"""What this classifier read, kept rather than reported and forgotten.

Storing turns the eval from a run into a dataset: what a configuration answered
stays readable, and a second configuration is paid for only where it has not
read. Safe because a claim resolves user-first — a reading on a hand-claimed
attempt never reaches the board.

What is stored is the reading, never the score. An aggregate is a derived view,
recomputed on every read.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.claims.classifier import DEFAULT, Configuration, request_hash
from algo_coach.claims.run import ABORT_AFTER, Failed, store
from algo_coach.claims.sample import recency
from algo_coach.claims.stale import readings_at
from algo_coach.log import AttemptLog
from algo_coach.schema import Attempt, Call, Problem, TechniqueClaim


class ReadResult(BaseModel):
    verdicts: dict[str, list[str]] = Field(default_factory=dict)  # attempt id -> techniques
    read: int = 0  # attempts this run paid a call for
    reused: int = 0  # answered from a stored reading
    undecided: int = 0  # named no candidate: stored, and never scored
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False
    # What the readings behind this result were charged, and how many of them
    # said. A reading stored before the field carries no price and is left out
    # of both, so the mean is over what is known rather than over a
    # denominator including readings that report nothing.
    cost: float = 0.0
    costed: int = 0
    # The calls behind the readings, so a report can join what only a call
    # holds. Ids rather than the tokens themselves: the doc keeps token counts
    # off a claim on purpose, and copying them here would be the same move one
    # layer along.
    call_ids: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    """One configuration's share of a run: what it must pay to read, and what
    has landed so far.

    Selecting is separated from asking so that one consumer can drive several
    configurations at once. The answers arrive interleaved, and each is folded
    into the state its own selection produced. That is also what keeps every
    append on the consuming thread, however many calls are in flight.
    """

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

    Which attempts are worth reading is the caller's: that is what the next
    comparison changes, and it is not this function's question.

    `limit` caps the calls, not the attempts — a stored reading is free, so a
    capped run adds to what earlier runs read rather than replacing it. What is
    still unread is taken newest first, as the backlog run takes it.

    Makes no call and writes nothing, so it needs neither a transport nor a
    log. A configuration whose readings all come from the log asks for nothing
    and is still a plan, with a total of zero.
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
            # A stored decline, kept as the verdict it is. The classifier read
            # the code and said none of the candidates apply, which contradicts
            # a claim naming some of them rather than failing to answer it.
            plan.result.verdicts[attempt.id] = []
            plan.result.undecided += 1
        plan.result.verdicts[attempt.id] = reading.techniques
        plan.result.reused += 1
        # Its own price, from the run that paid it. A rate applied now would
        # say what the reading would cost today rather than what it cost.
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
    """Fold one answer into the plan that asked for it, and say what to report.

    Writes on the calling thread, which is the one consumer however many calls
    are in flight. Returns the fields the verdict decides, leaving the counter
    and the reporting to the caller.

    A run of failures ends the plan rather than the run. A configuration this
    classifier cannot run fails identically on every attempt, and the eval set
    is the wrong place to learn that once — but a model that is broken says
    nothing about the endpoint, so the configurations beside it keep reading.
    """
    plan.answered += 1
    techniques, call = answer if answer is not None else ([], None)

    if failure is not None:
        # Broad on purpose: a refusal, a rate limit or a dropped connection is
        # one attempt's problem, and a run must not lose the ones behind it.
        plan.result.failed.append(Failed(attempt_id=attempt.id, reason=repr(failure)))
        plan.consecutive += 1
        if plan.consecutive == ABORT_AFTER:
            plan.result.aborted = True
        return {"reason": repr(failure)}

    # Answered, so the classifier is reachable — an undecided verdict is a
    # reading, not a failure.
    plan.consecutive = 0
    if call is not None:
        plan.result.call_ids.append(call.id)
        if call.cost is not None:
            plan.result.cost += call.cost
            plan.result.costed += 1
    if call is not None:
        # Stored whether or not it named anything, so no later run at this
        # configuration pays for the same question again.
        store(log, attempt.id, techniques, call)
    if not techniques:
        # Counted apart and scored all the same. Naming none of the candidates
        # is an answer, and a share that dropped it would reward declining:
        # every decline shrank the denominator it was measured against.
        plan.result.verdicts[attempt.id] = []
        plan.result.undecided += 1
        return {}
    plan.result.verdicts[attempt.id] = techniques
    plan.result.read += 1
    return {"techniques": techniques}
