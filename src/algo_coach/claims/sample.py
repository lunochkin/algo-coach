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
    # Claimed drops out after the collapse, not before: filtering first would
    # promote an older attempt and ask the same problem twice.
    collapsed = one_per_problem(eligible(attempts, problems, user_id=user_id, technique=technique))
    return [attempt for attempt in collapsed if attempt.id not in claimed]


def eligible(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    technique: str | None = None,
) -> list[Attempt]:
    """The user's attempts a claim could be made about: carrying their code,
    on a problem whose tags leave a choice.

    What a hand pass and the classifier both draw from — they differ in how
    many they take, not in what qualifies.
    """
    return [
        attempt
        for attempt in attempts
        if attempt.user_id == user_id
        and attempt.code
        and decides_something(problems.get(attempt.problem_id), technique)
    ]


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
