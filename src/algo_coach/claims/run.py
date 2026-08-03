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
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.mint import classifier_claim
from algo_coach.schema import Problem


class Failed(BaseModel):
    attempt_id: str
    reason: str


class ClassifyResult(BaseModel):
    classified: int = 0
    undecided: int = 0  # named none of the candidates; the fallback stands
    failed: list[Failed] = Field(default_factory=list)


def classify_backlog(
    client: Any,
    log: AttemptLog,
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    limit: int | None = None,
    technique: str | None = None,
) -> ClassifyResult:
    """Claim every attempt nothing has claimed yet.

    Newest first, so a run cut short by `limit` improves the numbers the board
    is showing rather than the oldest ones. Claims are appended as they are
    made and a claimed attempt is skipped, so a run resumes where the last one
    stopped instead of paying for it twice.
    """
    claimed = latest_by_attempt(log.claims())
    pending = [
        attempt
        for attempt in sorted(
            eligible(log.attempts(), problems, user_id=user_id, technique=technique),
            key=recency,
            reverse=True,
        )
        if attempt.id not in claimed
    ]

    result = ClassifyResult()
    for attempt in pending[:limit]:
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
            # A claim cannot say "none of these", and the fallback already
            # answers what the tags say.
            result.undecided += 1
            continue
        log.append_claim(
            classifier_claim(attempt.id, techniques, model=MODEL, prompt_version=PROMPT_VERSION)
        )
        result.classified += 1
    return result
