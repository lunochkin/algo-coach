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
from algo_coach.schema import Attempt

_ENGINE_OWNED = frozenset({"id", "user_id"})


def ingest_attempts(
    records: Iterable[Mapping], *, user_id: str, log: AttemptLog
) -> AttemptIngestResult:
    """Validate a pushed batch, stamp identity, append what is new.

    The contract, in the order it has to hold:

    - `user_id` comes from the adapter, never from the payload. A record
      carrying its own `user_id` or `id` has them dropped — identity is the
      engine's to assign.
    - `id` is minted here (uuid4 hex).
    - `external_id` is required and is the client's idempotency token.
      `(user_id, external_id)` already in the log means the record is a
      duplicate: counted, not appended, not an error.
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

        payload = engine_payload(
            raw, owned=_ENGINE_OWNED, values={"id": uuid.uuid4().hex, "user_id": user_id}
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
