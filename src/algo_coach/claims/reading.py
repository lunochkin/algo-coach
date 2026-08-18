"""What this classifier read, kept rather than reported and forgotten.

Storing turns the eval from a run into a dataset: what a configuration answered
stays readable, and a second configuration is paid for only where it has not
read. Safe because a claim resolves user-first — a reading on a hand-claimed
attempt never reaches the board.

What is stored is the reading, never the score. An aggregate is a derived view,
recomputed on every read.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.claims.classifier import DEFAULT, Configuration, request_hash
from algo_coach.claims.run import (
    ABORT_AFTER,
    CONCURRENCY,
    Failed,
    Progress,
    as_answered,
    read_one,
    store,
)
from algo_coach.claims.sample import recency
from algo_coach.claims.stale import readings_at
from algo_coach.log import AttemptLog
from algo_coach.schema import Attempt, Problem, TechniqueClaim


class ReadResult(BaseModel):
    verdicts: dict[str, list[str]] = Field(default_factory=dict)  # attempt id -> techniques
    read: int = 0  # attempts this run paid a call for
    reused: int = 0  # answered from a stored reading
    undecided: int = 0  # named no candidate: stored, and never scored
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False


def read(
    transport: Transport | None,
    log: AttemptLog,
    calls: CallLog,
    attempts: Sequence[Attempt],
    problems: Mapping[str, Problem],
    *,
    claims: Sequence[TechniqueClaim],
    configuration: Configuration = DEFAULT,
    limit: int | None = None,
    concurrency: int = CONCURRENCY,
    fresh: bool = False,
    on_progress: Callable[[Progress], None] | None = None,
) -> ReadResult:
    """What one classifier reads each attempt as, from the log where it can.

    Selection is the caller's: which attempts are worth reading is what the
    next configuration comparison changes, and it is not this loop's question.

    `limit` caps the calls, not the attempts — a stored reading is free, so a
    capped run adds to what earlier runs read rather than replacing it. What is
    still unread is taken newest first, as the backlog run takes it. A cap of
    zero pays for nothing, so `transport` is never reached and may be absent.
    """
    asked = {
        attempt.id: request_hash(problems[attempt.problem_id].techniques, attempt.code or "")
        for attempt in attempts
        if attempt.problem_id in problems
    }
    stored = {} if fresh else readings_at(claims, configuration, asked)
    result = ReadResult()

    unread: list[Attempt] = []
    for attempt in attempts:
        reading = stored.get(attempt.id)
        if reading is None:
            unread.append(attempt)
            continue
        if not reading.techniques:
            # A stored decline. Read again by nothing and scored by nothing —
            # missing evidence is not a disagreement.
            result.undecided += 1
            continue
        result.verdicts[attempt.id] = reading.techniques
        result.reused += 1

    asking = sorted(unread, key=recency, reverse=True)[:limit]

    def report(index: int, attempt: Attempt, title: str, **verdict: Any) -> None:
        if on_progress is not None:
            on_progress(
                Progress(
                    index=index, total=len(asking), attempt_id=attempt.id, title=title, **verdict
                )
            )

    consecutive = 0
    index = 0
    for attempt, answer, failure in as_answered(
        lambda attempt: read_one(
            transport, calls, attempt, problems[attempt.problem_id], configuration=configuration
        ),
        asking,
        concurrency=concurrency,
    ):
        index += 1
        problem = problems[attempt.problem_id]
        techniques, call = answer if answer is not None else ([], None)
        if failure is not None:
            # One attempt's problem, as in the backlog run: an eval that dies
            # on the first refusal reports nothing about the rest. A run of
            # them is a different fact — a configuration this classifier cannot
            # run fails identically on every attempt, and paying for the whole
            # eval set to learn it once is the same waste the backlog run
            # already refuses.
            result.failed.append(Failed(attempt_id=attempt.id, reason=repr(failure)))
            report(index, attempt, problem.title, reason=repr(failure))
            consecutive += 1
            if consecutive == ABORT_AFTER:
                result.aborted = True
                break
            continue
        consecutive = 0
        if not techniques:
            # Stored, so no later run at this configuration pays for it again,
            # and left out of the verdicts, so nothing scores it: the
            # classifier said the candidates do not cover the code, which is
            # missing evidence rather than a disagreement.
            if call is not None:
                store(log, attempt.id, techniques, call)
            result.undecided += 1
            report(index, attempt, problem.title)
            continue
        if call is not None:
            store(log, attempt.id, techniques, call)
        result.verdicts[attempt.id] = techniques
        result.read += 1
        report(index, attempt, problem.title, techniques=techniques)
    return result
