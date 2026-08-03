from collections.abc import Container, Iterable, Mapping
from datetime import datetime

from algo_coach.schema import Attempt, Problem


def claimable(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claimed: Container[str],
    *,
    user_id: str,
    technique: str | None = None,
) -> list[Attempt]:
    """The attempts a hand claim would decide something about.

    Unclaimed, carrying their code, one per problem, on a problem whose tags
    leave a choice to make. Ordered by problem id, so a caller that shuffles
    with a seed describes its sample by that seed rather than by the order the
    log happened to hold.
    """
    eligible = [
        attempt
        for attempt in attempts
        if attempt.user_id == user_id
        and attempt.code
        and decides_something(problems.get(attempt.problem_id), technique)
    ]
    # Claimed drops out after the collapse, not before: filtering first would
    # promote an older attempt and ask the same problem twice.
    return [attempt for attempt in one_per_problem(eligible) if attempt.id not in claimed]


def one_per_problem(attempts: Iterable[Attempt]) -> list[Attempt]:
    """Each problem's latest attempt, ordered by problem id.

    A retry asks the identical question — same solution, same candidate tags —
    so counting both would weight that problem twice. `(finished_at, id)` is
    the order the drill loop reads a sitting in, so latest means one thing
    wherever the log is grouped.
    """
    latest: dict[str, Attempt] = {}
    for attempt in sorted(attempts, key=recency):
        latest[attempt.problem_id] = attempt
    return [latest[problem_id] for problem_id in sorted(latest)]


def recency(attempt: Attempt) -> tuple[datetime, str]:
    return attempt.finished_at, attempt.id


def decides_something(problem: Problem | None, technique: str | None) -> bool:
    """A single-tag problem needs no claim — the fallback already answers it,
    and a claim there would assert what nothing disputes."""
    if problem is None or len(problem.techniques) < 2:
        return False
    return technique is None or technique in problem.techniques
