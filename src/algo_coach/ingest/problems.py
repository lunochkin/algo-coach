import uuid
from collections.abc import Iterable, Mapping

from pydantic import ValidationError

from algo_coach.ingest.result import (
    MISSING_EXTERNAL_ID,
    ProblemIngestResult,
    Rejected,
    engine_payload,
    external_id_of,
    reason,
)
from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem, ProblemOwner
from algo_coach.techniques import map_tags

_ENGINE_OWNED = frozenset({"id", "user_id", "owner", "techniques"})


def ingest_problems(
    records: Iterable[Mapping], *, user_id: str, store: ProblemStore
) -> ProblemIngestResult:
    """Validate a pushed batch of problems, stamp provenance, upsert each one.

    Where this differs from attempts:

    - `owner` is stamped `USER` by this path and is never read from the
      payload, the same rule as identity.
    - `techniques` is engine-derived and is dropped if a client sends it. The
      payload's platform tags land in `source_tags` verbatim, and codes are
      re-derived from them on every push, so a mapping change reaches problems
      already in the store.
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
        external_id = external_id_of(raw)
        if external_id is None:
            result.rejected.append(Rejected(index=index, reason=MISSING_EXTERNAL_ID))
            continue

        existing = store.by_external(user_id, external_id)
        payload = engine_payload(
            raw,
            owned=_ENGINE_OWNED,
            values={
                "id": existing.id if existing else uuid.uuid4().hex,
                "external_id": external_id,
                "user_id": user_id,
                "owner": ProblemOwner.USER,
            },
        )

        try:
            problem = Problem.model_validate(payload)
        except ValidationError as exc:
            result.rejected.append(Rejected(index=index, reason=reason(exc)))
            continue

        problem = problem.model_copy(update={"techniques": map_tags(problem.source_tags)})

        store.put(problem)
        if existing:
            result.updated += 1
        else:
            result.ingested += 1

    return result
