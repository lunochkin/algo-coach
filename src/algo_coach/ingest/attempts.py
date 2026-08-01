import uuid
from collections.abc import Iterable, Mapping

from pydantic import ValidationError

from algo_coach.ingest.result import (
    MISSING_EXTERNAL_ID,
    AttemptIngestResult,
    Rejected,
    engine_payload,
    external_id_of,
    reason,
)
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, AttemptOrigin

_ENGINE_OWNED = frozenset({"id", "user_id", "problem_id", "origin"})
# Consumed by ingest to resolve the reference; never stored on the record.
_PAYLOAD_ONLY = frozenset({"problem_external_id"})

MISSING_PROBLEM_REF = "problem_external_id is required on the push path"
UNKNOWN_PROBLEM = "problem_external_id names a problem not in the store"


def ingest_attempts(
    records: Iterable[Mapping],
    *,
    user_id: str,
    log: AttemptLog,
    problems: ProblemStore,
) -> AttemptIngestResult:
    """Validate a pushed batch, stamp identity, append what is new.

    - Identity is the engine's: `id`, `user_id`, `problem_id` and `origin` are
      stamped here, and payload values for them dropped.
    - `external_id` is the client's idempotency token, required. A pair already
      in the log is a duplicate: counted, not appended, not an error.
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
        external_id = external_id_of(raw)
        if external_id is None:
            result.rejected.append(Rejected(index=index, reason=MISSING_EXTERNAL_ID))
            continue

        if external_id in seen:
            result.duplicates += 1
            continue

        problem_ref = raw.get("problem_external_id")
        if not isinstance(problem_ref, str) or not problem_ref:
            result.rejected.append(Rejected(index=index, reason=MISSING_PROBLEM_REF))
            continue

        problem = problems.by_external(user_id, problem_ref)
        if problem is None:
            result.rejected.append(Rejected(index=index, reason=UNKNOWN_PROBLEM))
            continue

        payload = engine_payload(
            raw,
            owned=_ENGINE_OWNED | _PAYLOAD_ONLY,
            values={
                "id": uuid.uuid4().hex,
                "user_id": user_id,
                "problem_id": problem.id,
                "origin": AttemptOrigin.PUSH,
            },
        )
        try:
            attempt = Attempt.model_validate(payload)
        except ValidationError as exc:
            result.rejected.append(Rejected(index=index, reason=reason(exc)))
            continue

        log.append_attempt(attempt)
        seen.add(external_id)
        result.ingested += 1

    return result
