"""The classifier over the stored log.

Every attempt carries its code, so the backlog is classifiable today — the
loop's own claims reach only what it touched, and the board's numbers are read
from all of it.
"""

from collections.abc import Callable, Mapping
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.claims.classifier import MODEL, PROMPT_VERSION, classify
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


def classify_backlog(
    client: Any,
    log: AttemptLog,
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    limit: int | None = None,
    technique: str | None = None,
    redo: bool = False,
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
            if attempt.id in standing
            and is_stale(standing[attempt.id], model=MODEL, prompt_version=PROMPT_VERSION)
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
    for index, attempt in enumerate(asking, start=1):
        problem = problems[attempt.problem_id]
        try:
            techniques = classify(client, problem.techniques, attempt.code or "")
        except Exception as exc:
            # Broad on purpose: a refusal, a rate limit or a dropped connection
            # is one attempt's problem, and a backlog run must not lose the
            # ones behind it.
            result.failed.append(Failed(attempt_id=attempt.id, reason=repr(exc)))
            report(index, attempt, problem.title, reason=repr(exc))
            consecutive += 1
            if consecutive == ABORT_AFTER:
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
        # Written even when the verdict is unchanged: the record names the
        # classifier that reached it, so an unwritten agreement would stay
        # stale and be paid for again on every run.
        log.append_claim(
            classifier_claim(attempt.id, techniques, model=MODEL, prompt_version=PROMPT_VERSION)
        )
        if attempt.id in superseding:
            result.redone += 1
        else:
            result.classified += 1
        report(index, attempt, problem.title, techniques=techniques)
    return result
