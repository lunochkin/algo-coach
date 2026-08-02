from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime

from pydantic import BaseModel

from algo_coach.schema import Attempt, Problem

# Sorts ahead of any real attempt, so never attempted ranks stalest.
_NEVER = datetime.min.replace(tzinfo=UTC)


class ProblemRow(BaseModel):
    """A problem offered for a drill, with the history behind the offer.

    Carries the problem itself: the loop hands over its URL, and re-looking it
    up by id would be the caller doing what this already did.
    """

    problem: Problem
    attempt_count: int
    solved_count: int
    # None when never attempted — nothing has been retrieved, so nothing is
    # stale yet, and it ranks ahead of everything that has.
    last_attempt_at: datetime | None = None


def candidates(
    technique: str, problems: Iterable[Problem], attempts: Iterable[Attempt]
) -> list[ProblemRow]:
    """What could be drilled for a technique, least recently attempted first.

    Membership is the problem's own techniques, not the claims on its attempts:
    selection asks what a problem could exercise, which is what a tag says,
    while a claim says what one past solution did. A problem nobody has
    attempted is a candidate on the same terms as one attempted last year.

    Ranked by staleness, lowest solve rate breaking a tie — the row a retrieval
    drill wants first — and by problem id where both are equal, so two renders
    of the same log offer the same order.
    """
    by_problem: dict[str, list[Attempt]] = defaultdict(list)
    for attempt in attempts:
        by_problem[attempt.problem_id].append(attempt)

    rows = [
        _row(problem, by_problem[problem.id])
        for problem in problems
        if technique in problem.techniques
    ]
    return sorted(rows, key=_staleness)


def _row(problem: Problem, attempts: list[Attempt]) -> ProblemRow:
    return ProblemRow(
        problem=problem,
        attempt_count=len(attempts),
        solved_count=sum(attempt.solved for attempt in attempts),
        last_attempt_at=max((attempt.finished_at for attempt in attempts), default=None),
    )


def _staleness(row: ProblemRow) -> tuple[datetime, float, str]:
    solved_share = row.solved_count / row.attempt_count if row.attempt_count else 0.0
    return (row.last_attempt_at or _NEVER, solved_share, row.problem.id)
