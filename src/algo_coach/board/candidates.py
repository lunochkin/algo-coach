from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime

from pydantic import BaseModel

from algo_coach.schema import Attempt, Problem

# Sorts ahead of any real attempt, so never attempted ranks stalest.
NEVER = datetime.min.replace(tzinfo=UTC)


class ProblemRow(BaseModel):
    """A problem offered for a drill, with the history behind the offer."""

    problem: Problem
    attempt_count: int
    solved_count: int
    last_attempt_at: datetime | None = None


# problem id breaks a remaining tie, so two renders of one log offer the same
# order
def every(problems: Iterable[Problem], attempts: Iterable[Attempt]) -> list[ProblemRow]:
    """Every served problem, least recently attempted first."""
    by_problem: dict[str, list[Attempt]] = defaultdict(list)
    for attempt in attempts:
        by_problem[attempt.problem_id].append(attempt)

    rows = [problem_row(problem, by_problem[problem.id]) for problem in problems if problem.served]
    return sorted(rows, key=_staleness)


# membership is a served problem's own techniques, never the claims on its
# attempts
def candidates(
    technique: str, problems: Iterable[Problem], attempts: Iterable[Attempt]
) -> list[ProblemRow]:
    """What could be drilled for a technique, in the order `every` gives."""
    return [row for row in every(problems, attempts) if technique in row.problem.techniques]


def problem_row(problem: Problem, attempts: Iterable[Attempt]) -> ProblemRow:
    """One problem with the history behind it, as a candidates row carries."""
    attempts = list(attempts)
    return ProblemRow(
        problem=problem,
        attempt_count=len(attempts),
        solved_count=sum(attempt.solved for attempt in attempts),
        last_attempt_at=max((attempt.finished_at for attempt in attempts), default=None),
    )


def _staleness(row: ProblemRow) -> tuple[datetime, float, str]:
    solved_share = row.solved_count / row.attempt_count if row.attempt_count else 0.0
    return (row.last_attempt_at or NEVER, solved_share, row.problem.id)
