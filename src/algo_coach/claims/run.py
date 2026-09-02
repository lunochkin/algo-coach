"""The classifier over the stored log."""

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport
from algo_coach.claims.sample import eligible, recency
from algo_coach.claims.stale import is_stale
from algo_coach.classifier import DEFAULT, Configuration, classify, request_hash
from algo_coach.log import AttemptLog
from algo_coach.mint import classifier_claim
from algo_coach.runs import ABORT_AFTER, CONCURRENCY, as_answered
from algo_coach.schema import Attempt, Call, Problem
from algo_coach.techniques import standing_claims


class Failed(BaseModel):
    attempt_id: str
    reason: str


class Progress(BaseModel):
    """One attempt, answered. Reported as the run goes, since a call per attempt
    makes a backlog run minutes long."""

    index: int  # 1-based, over what this run will ask about
    total: int
    attempt_id: str
    title: str
    techniques: list[str] = Field(default_factory=list)  # empty when undecided
    reason: str | None = None  # the failure, when there was one


class ClassifyResult(BaseModel):
    classified: int = 0
    redone: int = 0  # stale machine claims superseded by this classifier
    undecided: int = 0  # named none of the candidates; the fallback stands
    failed: list[Failed] = Field(default_factory=list)
    aborted: bool = False

    @property
    def written(self) -> int:
        return self.classified + self.redone


def read_one(
    transport: Transport,
    calls: CallLog,
    attempt: Attempt,
    problem: Problem,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """Makes the call and writes no claim, so several can run at once. The claim
    is the caller's, and the claims log has one writer."""
    return classify(
        transport, calls, problem.techniques, attempt.code or "", configuration=configuration
    )


def store(
    log: AttemptLog,
    attempt_id: str,
    techniques: Sequence[str],
    call: Call,
) -> None:
    """Append what a classifier read, on the calling thread.

    Only ever after a call: a reading served from an earlier claim was already
    written by the run that paid for it, and appending it again would say the
    question was asked twice.
    """
    log.append_claim(
        classifier_claim(
            attempt_id,
            list(techniques),
            model=call.model,
            effort=call.effort,
            prompt_hash=call.prompt_hash,
            call_id=call.id,
            pin=call.pin or "",
            temperature=call.temperature,
            provider=call.provider,
            cost=call.cost,
        )
    )


def ask(
    transport: Transport,
    log: AttemptLog,
    calls: CallLog,
    attempt: Attempt,
    problem: Problem,
    *,
    configuration: Configuration = DEFAULT,
) -> list[str]:
    """Classify one attempt and store the verdict, returning what was named.

    An empty verdict writes no claim; the call log still records that it was
    asked. Failures are the caller's.
    """
    techniques, call = read_one(transport, calls, attempt, problem, configuration=configuration)
    if techniques and call is not None:
        store(log, attempt.id, techniques, call)
    return techniques


def classify_backlog(
    transport: Transport,
    log: AttemptLog,
    calls: CallLog,
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    configuration: Configuration = DEFAULT,
    limit: int | None = None,
    technique: str | None = None,
    redo: bool = False,
    concurrency: int = CONCURRENCY,
    fresh: bool = False,
    on_progress: Callable[[Progress], None] | None = None,
) -> ClassifyResult:
    """Claim every unclaimed attempt, and with `redo`, every one an older
    classifier claimed.

    Newest first, and unclaimed before stale: a first claim buys a number the
    board does not have, where a re-derivation revises one it does. Claims are
    appended as they are made and a current one is skipped, so a run resumes
    where the last stopped. `on_progress` fires once per attempt asked about;
    reporting is the caller's.
    """
    standing = standing_claims(log.claims())
    candidates = sorted(
        eligible(log.attempts(), problems, user_id=user_id, technique=technique),
        key=recency,
        reverse=True,
    )
    # What each attempt would be sent now. A claim answering that exact question
    # is not stale however old it is; `fresh` asks again regardless.
    asked = {
        attempt.id: request_hash(problems[attempt.problem_id].techniques, attempt.code or "")
        for attempt in candidates
    }
    unclaimed = [attempt for attempt in candidates if attempt.id not in standing]
    stale = (
        [
            attempt
            for attempt in candidates
            if attempt.id in standing
            and (fresh or is_stale(standing[attempt.id], configuration, asked[attempt.id]))
        ]
        if redo
        else []
    )
    superseding = {attempt.id for attempt in stale}

    asking = (unclaimed + stale)[:limit]

    def report(index: int, attempt: Attempt, title: str, **verdict: Any) -> None:
        if on_progress is not None:
            on_progress(
                Progress(
                    index=index, total=len(asking), attempt_id=attempt.id, title=title, **verdict
                )
            )

    result = ClassifyResult()
    consecutive = 0
    index = 0
    for attempt, answer, failure in as_answered(
        lambda attempt: read_one(
            transport, calls, attempt, problems[attempt.problem_id], configuration=configuration
        ),
        asking,
        concurrency=concurrency,
    ):
        # Counted as answers arrive: with several calls in flight a position in
        # the order asked in jumps about, and a reader wants a count that climbs.
        index += 1
        problem = problems[attempt.problem_id]
        techniques, call = answer if answer is not None else ([], None)
        if failure is not None:
            # Broad on purpose: a refusal or a dropped connection is one
            # attempt's problem, and the run must not lose the ones behind it.
            result.failed.append(Failed(attempt_id=attempt.id, reason=repr(failure)))
            report(index, attempt, problem.title, reason=repr(failure))
            consecutive += 1
            if consecutive == ABORT_AFTER:
                # Consecutive by the order answered. What is in flight still
                # lands, so a broken key costs up to `concurrency` failures
                # rather than `ABORT_AFTER`.
                result.aborted = True
                break
            continue
        # Answered, so the classifier is reachable: an undecided verdict is a
        # reading, not a failure.
        consecutive = 0
        if not techniques:
            # Stored rather than dropped: the candidates did not cover the
            # code, and that answer holds while the question does not change.
            if call is not None:
                store(log, attempt.id, techniques, call)
            result.undecided += 1
            report(index, attempt, problem.title)
            continue
        if call is not None:
            store(log, attempt.id, techniques, call)
        if attempt.id in superseding:
            result.redone += 1
        else:
            result.classified += 1
        report(index, attempt, problem.title, techniques=techniques)
    return result
