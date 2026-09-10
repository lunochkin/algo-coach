from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime

from pydantic import BaseModel

from algo_coach.attempt_claims import resolve_techniques
from algo_coach.board.candidates import NEVER
from algo_coach.schema import Attempt, AttemptClaim, FailureMode, Problem, SelfLabel


class TechniqueRow(BaseModel):
    """One technique's progress, derived from the log on every read."""

    technique: str
    attempt_count: int
    solved_count: int
    last_attempt_at: datetime | None = None  # none on a technique nothing practised yet
    # Only the modes an attempt was labelled with; an unlabelled attempt
    # counts toward the row and toward no mode.
    self_labels: dict[FailureMode, int] = {}

    @property
    def unsolved_count(self) -> int:
        return self.attempt_count - self.solved_count


def per_technique(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claims: Mapping[str, AttemptClaim],
    labels: Mapping[str, SelfLabel],
) -> list[TechniqueRow]:
    """The drill board: one row per technique the log reaches, ordered by code.

    An attempt counts once in every technique it resolves to, and a defective
    problem's attempts count nowhere, solved or not. `problems` is keyed by
    problem id, `claims` and `labels` by attempt id; a missing problem raises
    rather than dropping the attempt.
    """
    grouped: dict[str, list[Attempt]] = defaultdict(list)
    for attempt in attempts:
        problem = problems[attempt.problem_id]
        if problem.defective:
            continue
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
    claims: Mapping[str, AttemptClaim],
) -> list[Attempt]:
    """The attempts `per_technique` reaches no row for, shown beside the
    rows. A defective problem's attempts are `excluded` instead."""
    return [
        attempt
        for attempt in attempts
        if not problems[attempt.problem_id].defective
        and not resolve_techniques(attempt, problems[attempt.problem_id], claims)
    ]


def excluded(attempts: Iterable[Attempt], problems: Mapping[str, Problem]) -> list[Attempt]:
    """The attempts a defective problem took off the board, still readable in
    the log."""
    return [attempt for attempt in attempts if problems[attempt.problem_id].defective]


def stalest_first(rows: Iterable[TechniqueRow], problems: Iterable[Problem]) -> list[TechniqueRow]:
    """The board the drill loop opens on: every row, and an empty one for each
    technique a served problem carries that no attempt reached. A technique
    never practised ranks stalest, and the code breaks a tie."""
    by_technique = {row.technique: row for row in rows}
    for problem in problems:
        for technique in problem.techniques if problem.served else []:
            by_technique.setdefault(
                technique, TechniqueRow(technique=technique, attempt_count=0, solved_count=0)
            )
    return sorted(
        by_technique.values(), key=lambda row: (row.last_attempt_at or NEVER, row.technique)
    )
