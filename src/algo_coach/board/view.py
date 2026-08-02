from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime

from pydantic import BaseModel, Field

from algo_coach.schema import Attempt, FailureMode, Problem, TechniqueClaim
from algo_coach.techniques import resolve_techniques


class TechniqueRow(BaseModel):
    """One technique's standing, derived from the log on every read. Never
    stored: an aggregate that outlived the records under it would be a second
    truth."""

    technique: str
    attempt_count: int
    solved_count: int
    last_attempt_at: datetime
    # Only the labels an attempt actually carried; an unlabelled attempt
    # counts toward the row and toward no mode.
    self_labels: dict[FailureMode, int] = Field(default_factory=dict)

    @property
    def unsolved_count(self) -> int:
        return self.attempt_count - self.solved_count


def per_technique(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claims: Mapping[str, TechniqueClaim],
) -> list[TechniqueRow]:
    """The drill board: one row per technique the log reaches, ordered by code.

    Each attempt is resolved through `resolve_techniques` and counted once in
    every technique it names — a solution using two techniques is evidence
    about both. An attempt resolving to no code produces no row: an unmapped
    tag blocks nothing and invents nothing.

    `problems` is keyed by the engine-minted id. A reference it cannot answer
    is a broken invariant, not an empty row.
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
                attempt.self_label for attempt in group if attempt.self_label is not None
            ),
        )
        for technique, group in sorted(grouped.items())
    ]


def ungrouped(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claims: Mapping[str, TechniqueClaim],
) -> list[Attempt]:
    """The attempts `per_technique` reaches no row for.

    Real work that the board cannot show: unmapped tags and unclaimed
    attempts leave no code to group by. Counted beside the rows so the
    omission is visible rather than silent.
    """
    return [
        attempt
        for attempt in attempts
        if not resolve_techniques(attempt, problems[attempt.problem_id], claims)
    ]
