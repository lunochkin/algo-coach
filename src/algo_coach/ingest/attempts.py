import uuid
from collections.abc import Iterable, Mapping

from pydantic import ValidationError

from algo_coach.ingest.result import AttemptIngestResult, Rejected, reason
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, AttemptOrigin, AttemptPush

UNKNOWN_PROBLEM = "problem_external_id names a problem not in the store"


def ingest_attempts(
    records: Iterable[Mapping],
    *,
    user_id: str,
    log: AttemptLog,
    problems: ProblemStore,
) -> AttemptIngestResult:
    """Validate a pushed batch, stamp identity, append what is new.

    - `AttemptPush` is the contract: identity and provenance have no field on
      it, so `id`, `user_id`, `problem_id` and `origin` can only be stamped
      here.
    - `external_id` is the client's idempotency token. A pair already in the
      log is a duplicate: counted, not appended, not an error.
    - `problem_external_id` is resolved to the minted `problem_id`. The log
      must not hold a reference nothing can follow, so an unresolvable one is
      rejected — push problems before their attempts.
    - A bad record is rejected by index and the batch continues, so one
      malformed line costs only itself.
    - Append-only: nothing here rewrites a record.
    """
    seen = {attempt.external_id for attempt in log.attempts() if attempt.user_id == user_id}
    result = AttemptIngestResult()

    for index, raw in enumerate(records):
        try:
            push = AttemptPush.model_validate(raw)
        except ValidationError as exc:
            result.rejected.append(Rejected(index=index, reason=reason(exc)))
            continue

        if push.external_id in seen:
            result.duplicates += 1
            continue

        problem = problems.by_external(user_id, push.problem_external_id)
        if problem is None:
            result.rejected.append(Rejected(index=index, reason=UNKNOWN_PROBLEM))
            continue

        attempt = Attempt(
            **push.model_dump(exclude={"problem_external_id"}),
            id=uuid.uuid4().hex,
            user_id=user_id,
            problem_id=problem.id,
            origin=AttemptOrigin.PUSH,
        )

        log.append_attempt(attempt)
        seen.add(push.external_id)
        result.ingested += 1

    return result
