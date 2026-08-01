import uuid
from collections.abc import Iterable, Mapping

from pydantic import ValidationError

from algo_coach.ingest.result import ProblemIngestResult, Rejected, reason
from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem, ProblemOwner, ProblemPush
from algo_coach.techniques import map_tags


def ingest_problems(
    records: Iterable[Mapping], *, user_id: str, store: ProblemStore
) -> ProblemIngestResult:
    """Validate a pushed batch of problems, stamp provenance, upsert each one.

    Where this differs from attempts:

    - `owner` is stamped `USER`, never read from the payload.
    - `techniques` has no field on `ProblemPush`: platform tags land in
      `source_tags` verbatim and codes are re-derived on every push, so a
      mapping change reaches problems already stored.
    - `(user_id, external_id)` identifies the problem across pushes, so a known
      pair refreshes the descriptive fields and counts as `updated`.
    - Identity survives that update — attempts already reference the `id`.
    """
    result = ProblemIngestResult()

    for index, raw in enumerate(records):
        try:
            push = ProblemPush.model_validate(raw)
        except ValidationError as exc:
            result.rejected.append(Rejected(index=index, reason=reason(exc)))
            continue

        existing = store.by_external(user_id, push.external_id)
        problem = Problem(
            **push.model_dump(),
            id=existing.id if existing else uuid.uuid4().hex,
            user_id=user_id,
            owner=ProblemOwner.USER,
            techniques=map_tags(push.source_tags),
        )

        store.put(problem)
        if existing:
            result.updated += 1
        else:
            result.ingested += 1

    return result
