import uuid
from collections.abc import Iterable, Mapping

from pydantic import BaseModel, Field, ValidationError

from algo_coach.log import AttemptLog
from algo_coach.schema import Attempt


class Rejected(BaseModel):
    index: int  # position in the pushed batch, so the client can find the line
    reason: str


class IngestResult(BaseModel):
    ingested: int = 0
    duplicates: int = 0
    rejected: list[Rejected] = Field(default_factory=list)


def ingest_attempts(
    records: Iterable[Mapping], *, user_id: str, log: AttemptLog
) -> IngestResult:
    """Validate a pushed batch, stamp identity, append what is new.

    The contract, in the order it has to hold:

    - `user_id` comes from the adapter, never from the payload. A record
      carrying its own `user_id` or `id` has them overwritten, not honoured —
      identity is the engine's to assign.
    - `id` is minted here (uuid4 hex).
    - `external_id` is required on this path and is the client's idempotency
      token. `(user_id, external_id)` already in the log means the record is a
      duplicate: counted, not appended, not an error.
    - A record that fails validation is rejected by index and does not stop the
      batch. Partial ingest is the point — one malformed line must not cost the
      attempts around it.
    - Ingest is append-only. Nothing here rewrites an existing record.
    """
    seen = {a.external_id for a in log.attempts() if a.user_id == user_id}
    result = IngestResult()

    for index, raw in enumerate(records):
        external_id = raw.get("external_id")
        if not isinstance(external_id, str) or not external_id:
            result.rejected.append(
                Rejected(index=index, reason="external_id is required on the push path")
            )
            continue

        if external_id in seen:
            result.duplicates += 1
            continue

        try:
            attempt = Attempt.model_validate(
                dict(raw) | {"id": uuid.uuid4().hex, "user_id": user_id}
            )
        except ValidationError as exc:
            result.rejected.append(Rejected(index=index, reason=_reason(exc)))
            continue

        log.append_attempt(attempt)
        seen.add(external_id)
        result.ingested += 1

    return result


def _reason(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
