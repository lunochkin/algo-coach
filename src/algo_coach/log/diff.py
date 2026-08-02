from collections.abc import Collection, Iterable

from algo_coach.schema import Attempt


def appeared(
    attempts: Iterable[Attempt], *, problem_id: str, known: Collection[str]
) -> list[Attempt]:
    """The attempts on a problem that were not in the log when `known` was taken.

    How the drill loop finds what a push added: it snapshots the ids it can
    already see, waits, and asks again. Exact rather than heuristic — no
    timestamp window has to guess which submission was the drill's, and a
    backfilled attempt pushed mid-drill counts too, since new to the log is
    the only question being asked.

    Chronological by `finished_at`, id breaking a tie, so a sitting is asked
    about in the order it happened.
    """
    fresh = [
        attempt
        for attempt in attempts
        if attempt.problem_id == problem_id and attempt.id not in known
    ]
    return sorted(fresh, key=lambda attempt: (attempt.finished_at, attempt.id))
