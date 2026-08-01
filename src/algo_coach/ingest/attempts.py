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
from algo_coach.schema import Attempt

_ENGINE_OWNED = frozenset({"id", "user_id", "problem_id"})
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

    The contract, in the order it has to hold:

    - `user_id` comes from the adapter, never from the payload. A record
      carrying its own `user_id`, `id` or `problem_id` has them dropped —
      identity is the engine's to assign.
    - `id` is minted here (uuid4 hex).
    - `external_id` is required and is the client's idempotency token.
      `(user_id, external_id)` already in the log means the record is a
      duplicate: counted, not appended, not an error.
    - `problem_external_id` names the problem as the origin platform does; the
      engine resolves it to the minted `problem_id` it stores. A client cannot
      know that id, and the log must not hold a reference nothing can follow,
      so an unresolvable one is rejected. Push problems before their attempts.
    - A record that fails validation is rejected by index and does not stop the
      batch. Partial ingest is the point — one malformed line must not cost the
      attempts around it.
    - Ingest is append-only. Nothing here rewrites an existing record.
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
