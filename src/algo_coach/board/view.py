from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime

from pydantic import BaseModel, Field

from algo_coach.schema import Attempt, FailureMode, Problem, SelfLabel, TechniqueClaim
from algo_coach.techniques import resolve_techniques


class TechniqueRow(BaseModel):
    """One technique's standing, derived from the log on every read."""

    technique: str
    attempt_count: int
    solved_count: int
    last_attempt_at: datetime
    # Only the modes an attempt was labelled with; an unlabelled attempt
    # counts toward the row and toward no mode.
    self_labels: dict[FailureMode, int] = Field(default_factory=dict)

    @property
    def unsolved_count(self) -> int:
        return self.attempt_count - self.solved_count


def per_technique(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claims: Mapping[str, TechniqueClaim],
    labels: Mapping[str, SelfLabel],
) -> list[TechniqueRow]:
    """The drill board: one row per technique the log reaches, ordered by code.

    An attempt counts once in every technique it resolves to. `problems` is
    keyed by problem id, `claims` and `labels` by attempt id; a missing problem
    raises rather than dropping the attempt.
    """
    grouped: dict[str, list[Attempt]] = defaultdict(list)
    for attempt in attempts:
        problem = problems[attempt.problem_id]
        for technique in resolve_techniques(attempt, problem, claims):
            grouped[technique].append(attempt)

    return [
        TechniqueRow(
            technique=technique,
            attempt_count=len(group),
            solved_count=sum(attempt.solved for attempt in group),
            last_attempt_at=max(attempt.finished_at for attempt in group),
            self_labels=Counter(
                labels[attempt.id].mode for attempt in group if attempt.id in labels
            ),
        )
        for technique, group in sorted(grouped.items())
    ]


def ungrouped(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claims: Mapping[str, TechniqueClaim],
) -> list[Attempt]:
    """The attempts `per_technique` reaches no row for, shown beside the rows."""
    return [
        attempt
        for attempt in attempts
        if not resolve_techniques(attempt, problems[attempt.problem_id], claims)
    ]
