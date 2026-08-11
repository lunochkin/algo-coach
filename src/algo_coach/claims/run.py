"""The classifier over the stored log.

Every attempt carries its code, so the backlog is classifiable today — the
loop's own claims reach only what it touched, and the board's numbers are read
from all of it.
"""

from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from itertools import islice
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.claims.classifier import DEFAULT, PROMPT_HASH, Configuration, classify
from algo_coach.claims.sample import eligible, recency
from algo_coach.claims.stale import is_stale
from algo_coach.log import AttemptLog
from algo_coach.mint import classifier_claim
from algo_coach.schema import Attempt, Problem
from algo_coach.techniques import standing_claims

# Consecutive failures that mean the run is broken rather than unlucky. A
# refusal or a rate limit hits one attempt; a rejected key or a spent quota
# hits every one, and reporting that per attempt buries it.
ABORT_AFTER = 3

# One call at a time. A backlog run is minutes of waiting on a network, so the
# default is the cautious one and the caller raises it: the binding limit is
# input tokens per minute, not requests, since every call carries the code and
# the criteria and thinks before it answers.
CONCURRENCY = 1


class Failed(BaseModel):
    attempt_id: str
    reason: str


class Progress(BaseModel):
    """One attempt, answered. Reported as the run goes rather than counted at
    the end, since a call per attempt makes a backlog run minutes long."""

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
    client: Any,
    attempt: Attempt,
    problem: Problem,
    *,
    configuration: Configuration = DEFAULT,
) -> list[str]:
    """What one classifier reads one attempt as. Makes the call and nothing
    else, so it is safe to run several at once — the write is the caller's,
    and the log has one writer however many calls are in flight."""
    return classify(client, problem.techniques, attempt.code or "", configuration=configuration)


def store(
    log: AttemptLog,
    attempt_id: str,
    techniques: Sequence[str],
    *,
    configuration: Configuration = DEFAULT,
) -> None:
    """Append what a classifier read, on the calling thread.

    Written even when the verdict is unchanged: the record names the classifier
    that reached it, so an unwritten agreement would stay stale and be paid for
    again on every later run.

    The hash is this build's rather than the configuration's: a caller names
    which classifier to run, never which prompt text it sent.
    """
    log.append_claim(
        classifier_claim(
            attempt_id,
            list(techniques),
            model=configuration.model,
            effort=configuration.effort,
            prompt_version=configuration.prompt_version,
            prompt_hash=PROMPT_HASH,
        )
    )


def ask(
    client: Any,
    log: AttemptLog,
    attempt: Attempt,
    problem: Problem,
    *,
    configuration: Configuration = DEFAULT,
) -> list[str]:
    """Classify one attempt and store the verdict, returning what was named.

    An empty verdict is undecided rather than a claim: a claim cannot say "none
    of these", so nothing is written and whatever already answers the attempt
    keeps answering it. Failures are the caller's — a backlog run aborts on a
    broken key and an eval does not.
    """
    techniques = read_one(client, attempt, problem, configuration=configuration)
    if techniques:
        store(log, attempt.id, techniques, configuration=configuration)
    return techniques


def as_answered[T, R](
    work: Callable[[T], R],
    items: Sequence[T],
    *,
    concurrency: int = CONCURRENCY,
) -> Iterator[tuple[T, R | None, Exception | None]]:
    """Run `work` over `items`, yielding each as it finishes.

    Completion order, not the order asked in — which is safe for what the
    callers do with it. A claim ties with another only on `created_at`, broken
    by append order, and that decides between two claims on one attempt; a run
    makes at most one per attempt, so nothing a run writes can race itself.

    Submission is bounded rather than all at once: a consumer that stops early
    — a run aborting on a rejected key — must not have paid for the tail.
    Closing the iterator cancels what has not started, and lets what is in
    flight finish, since an API call cannot be taken back.

    One worker is the serial path outright, not a pool of one: the ordinary run
    should not depend on a thread pool to be correct.
    """
    if concurrency <= 1:
        for item in items:
            try:
                yield item, work(item), None
            except Exception as exc:
                yield item, None, exc
        return

    queued = iter(items)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        running = {pool.submit(work, item): item for item in islice(queued, concurrency)}
        try:
            while running:
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    item = running.pop(future)
                    failure = future.exception()
                    yield item, (None if failure else future.result()), failure
                    running.update({pool.submit(work, nxt): nxt for nxt in islice(queued, 1)})
        finally:
            pool.shutdown(cancel_futures=True)


def classify_backlog(
    client: Any,
    log: AttemptLog,
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    configuration: Configuration = DEFAULT,
    limit: int | None = None,
    technique: str | None = None,
    redo: bool = False,
    concurrency: int = CONCURRENCY,
    on_progress: Callable[[Progress], None] | None = None,
) -> ClassifyResult:
    """Claim every attempt nothing has claimed yet, and with `redo`, every one
    an older classifier claimed.

    `on_progress` is called once per attempt asked about, so a caller can
    report a run as it goes. Reporting is the caller's, not this loop's: the
    CLI prints, a web API would not.

    Newest first, so a run cut short by `limit` improves the numbers the board
    is showing rather than the oldest ones. Claims are appended as they are
    made and a current claim is skipped, so a run resumes where the last one
    stopped instead of paying for it twice.

    Unclaimed before stale, since a first claim buys a number the board does
    not have and a re-derivation only revises one it does. A hand-claimed
    attempt is neither, and is skipped as an economy rather than as what
    protects the eval — a verdict there could never stand, since the user's
    claim wins on read. What protects the eval is the reader.
    """
    standing = standing_claims(log.claims())
    candidates = sorted(
        eligible(log.attempts(), problems, user_id=user_id, technique=technique),
        key=recency,
        reverse=True,
    )
    unclaimed = [attempt for attempt in candidates if attempt.id not in standing]
    stale = (
        [
            attempt
            for attempt in candidates
            if attempt.id in standing and is_stale(standing[attempt.id], configuration)
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
    for attempt, techniques, failure in as_answered(
        lambda attempt: read_one(
            client, attempt, problems[attempt.problem_id], configuration=configuration
        ),
        asking,
        concurrency=concurrency,
    ):
        # Counted as answers arrive rather than taken from the order asked in:
        # with several calls in flight a position in that order jumps about,
        # and what a reader wants is a count that climbs.
        index += 1
        problem = problems[attempt.problem_id]
        if failure is not None:
            # Broad on purpose: a refusal, a rate limit or a dropped connection
            # is one attempt's problem, and a backlog run must not lose the
            # ones behind it.
            result.failed.append(Failed(attempt_id=attempt.id, reason=repr(failure)))
            report(index, attempt, problem.title, reason=repr(failure))
            consecutive += 1
            if consecutive == ABORT_AFTER:
                # Consecutive by the order answered. What is already in flight
                # still lands, so a broken key costs up to `concurrency`
                # failures rather than `ABORT_AFTER` — time on calls that fail
                # before they are billed, which is the price of not waiting.
                result.aborted = True
                break
            continue
        # Answered, so the classifier is reachable — an undecided verdict is a
        # reading, not a failure.
        consecutive = 0
        if not techniques:
            # A claim cannot say "none of these", so what already answers the
            # attempt keeps answering it: the tags, or the older claim being
            # re-derived. Both leave it pending for the next run.
            result.undecided += 1
            report(index, attempt, problem.title)
            continue
        store(log, attempt.id, techniques, configuration=configuration)
        if attempt.id in superseding:
            result.redone += 1
        else:
            result.classified += 1
        report(index, attempt, problem.title, techniques=techniques)
    return result
