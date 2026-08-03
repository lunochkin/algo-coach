"""The classifier over the stored log.

Every attempt carries its code, so the backlog is classifiable today — the
loop's own claims reach only what it touched, and the board's numbers are read
from all of it.
"""

from collections.abc import Mapping
from typing import Any

from pydantic import BaseModel, Field

from algo_coach.claims.classifier import MODEL, PROMPT_VERSION, classify
from algo_coach.claims.sample import eligible, recency
from algo_coach.claims.stale import is_stale
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.mint import classifier_claim
from algo_coach.schema import Problem


class Failed(BaseModel):
    attempt_id: str
    reason: str


class ClassifyResult(BaseModel):
    classified: int = 0
    redone: int = 0  # stale machine claims superseded by this classifier
    undecided: int = 0  # named none of the candidates; the fallback stands
    failed: list[Failed] = Field(default_factory=list)

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
) -> ClassifyResult:
    """Claim every attempt nothing has claimed yet, and with `redo`, every one
    an older classifier claimed.

    Newest first, so a run cut short by `limit` improves the numbers the board
    is showing rather than the oldest ones. Claims are appended as they are
    made and a current claim is skipped, so a run resumes where the last one
    stopped instead of paying for it twice.

    Unclaimed before stale, since a first claim buys a number the board does
    not have and a re-derivation only revises one it does. A user's claim is
    neither: it is what the classifier is corrected by.
    """
    standing = latest_by_attempt(log.claims())
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

    result = ClassifyResult()
    for attempt in (unclaimed + stale)[:limit]:
        problem = problems[attempt.problem_id]
        try:
            techniques = classify(client, problem.techniques, attempt.code or "")
        except Exception as exc:
            # Broad on purpose: a refusal, a rate limit or a dropped connection
            # is one attempt's problem, and a backlog run must not lose the
            # ones behind it.
            result.failed.append(Failed(attempt_id=attempt.id, reason=repr(exc)))
            continue
        if not techniques:
            # A claim cannot say "none of these", so what already answers the
            # attempt keeps answering it: the tags, or the older claim being
            # re-derived. Both leave it pending for the next run.
            result.undecided += 1
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
    return result
