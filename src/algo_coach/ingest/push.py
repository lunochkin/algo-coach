import uuid
from collections.abc import Iterable, Mapping

from pydantic import BaseModel, Field, ValidationError

from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Attempt, Problem, ProblemOwner

# Fields the engine assigns; a client sending them is ignored, not trusted.
_ENGINE_OWNED = frozenset({"id", "user_id", "owner", "techniques"})


class Rejected(BaseModel):
    index: int  # position in the pushed batch, so the client can find the line
    reason: str


class IngestResult(BaseModel):
    ingested: int = 0
    duplicates: int = 0
    rejected: list[Rejected] = Field(default_factory=list)


class ProblemIngestResult(BaseModel):
    """Problems are a mutable cache, so a re-push updates rather than
    duplicates — the counter that means "no-op" for attempts means "refreshed"
    here."""

    ingested: int = 0
    updated: int = 0
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


def ingest_problems(
    records: Iterable[Mapping], *, user_id: str, store: ProblemStore
) -> ProblemIngestResult:
    """Validate a pushed batch of problems, stamp provenance, upsert each one.

    Where this differs from attempts:

    - `owner` is stamped `USER` by this path and is never read from the
      payload, the same rule as identity.
    - `techniques` is engine-derived and is dropped if a client sends it. The
      payload's platform tags land in `source_tags` verbatim; codes come from
      the engine's mapping, once that exists.
    - `(user_id, external_id)` identifies the problem across pushes. A known
      pair is an update, not a duplicate: the descriptive fields — title,
      title_slug, url, platform, source_tags, difficulty — are refreshed from
      the payload, counted in `updated`.
    - Identity never moves on update. The engine-minted `id`, `owner`,
      `user_id`, and `external_id` of an existing problem survive a re-push,
      because attempts already reference that `id`.
    - As with attempts, `external_id` is required here, a bad record is
      rejected by index, and the rest of the batch still lands.
    """
    result = ProblemIngestResult()

    for index, raw in enumerate(records):
        external_id = raw.get("external_id")
        if not isinstance(external_id, str) or not external_id:
            result.rejected.append(
                Rejected(index=index, reason="external_id is required on the push path")
            )
            continue

        existing = store.by_external(user_id, external_id)
        payload = {key: value for key, value in raw.items() if key not in _ENGINE_OWNED}
        payload |= {
            "id": existing.id if existing else uuid.uuid4().hex,
            "external_id": external_id,
            "user_id": user_id,
            "owner": ProblemOwner.USER,
            "techniques": existing.techniques if existing else [],
        }

        try:
            problem = Problem.model_validate(payload)
        except ValidationError as exc:
            result.rejected.append(Rejected(index=index, reason=_reason(exc)))
            continue

        store.put(problem)
        if existing:
            result.updated += 1
        else:
            result.ingested += 1

    return result


def _reason(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in exc.errors()
    )
