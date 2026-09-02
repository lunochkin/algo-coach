import random
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime

from algo_coach.schema import Attempt, ClaimSource, Problem, TechniqueClaim


def claimable(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claimed: Mapping[str, TechniqueClaim],
    *,
    user_id: str,
    technique: str | None = None,
    seed: int = 0,
) -> list[Attempt]:
    """The attempts a hand claim would decide something about, in the order to
    ask about them. A machine claim does not take one out of the pool; only the
    user's own answer does. Spread against the claims already made rather than
    within the batch, since the eval set is grown and never redrawn."""
    # Collapse before the filter, or an older attempt is promoted and the same
    # problem asked about twice.
    collapsed = one_per_problem(eligible(attempts, problems, user_id=user_id, technique=technique))
    answered = [attempt for attempt in collapsed if answered_by_hand(claimed.get(attempt.id))]
    return spread(
        [attempt for attempt in collapsed if not answered_by_hand(claimed.get(attempt.id))],
        problems,
        # What the answered attempts covered: the sample joins them.
        covered=Counter(
            code for attempt in answered for code in problems[attempt.problem_id].techniques
        ),
        seed=seed,
    )


def answered_by_hand(claim: TechniqueClaim | None) -> bool:
    return claim is not None and claim.source is ClaimSource.USER


def spread(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    *,
    covered: Mapping[str, int] | None = None,
    seed: int = 0,
) -> list[Attempt]:
    """The pool ordered so no single technique carries the estimate.

    Each step takes an attempt on the technique covered least so far; an attempt
    counts toward every technique its problem carries, so what is levelled is
    coverage rather than draws. Shuffled within a technique by `seed`. `covered`
    is what the order starts from, and it reorders rather than filters.
    """
    pool = list(attempts)
    random.Random(seed).shuffle(pool)

    buckets: dict[str, list[Attempt]] = defaultdict(list)
    for attempt in pool:
        for code in problems[attempt.problem_id].techniques:
            buckets[code].append(attempt)

    counts: Counter[str] = Counter(covered)
    taken: set[str] = set()
    cursors: Counter[str] = Counter()

    def untaken(code: str) -> Attempt | None:
        # The cursor never goes back, so the scan is paid once per attempt
        # rather than once per step.
        bucket = buckets[code]
        while cursors[code] < len(bucket) and bucket[cursors[code]].id in taken:
            cursors[code] += 1
        return bucket[cursors[code]] if cursors[code] < len(bucket) else None

    order: list[Attempt] = []
    while True:
        # Sorted, so the code breaks a tie on coverage and the order is the
        # seed's alone.
        live = [
            (code, attempt) for code in sorted(buckets) if (attempt := untaken(code)) is not None
        ]
        if not live:
            return order
        _, drawn = min(live, key=lambda pair: counts[pair[0]])
        taken.add(drawn.id)
        order.append(drawn)
        counts.update(problems[drawn.problem_id].techniques)


def eligible(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    *,
    user_id: str,
    technique: str | None = None,
) -> list[Attempt]:
    """The user's attempts a claim could be made about, which is what a hand pass
    and the classifier both draw from."""
    return [
        attempt
        for attempt in attempts
        if attempt.user_id == user_id
        and attempt.code
        and decides_something(problems.get(attempt.problem_id), technique)
    ]


def one_per_problem(attempts: Iterable[Attempt]) -> list[Attempt]:
    """Each problem's latest attempt, by `(finished_at, id)` — the order the
    drill loop reads a sitting in, so latest means one thing everywhere."""
    latest: dict[str, Attempt] = {}
    for attempt in sorted(attempts, key=recency):
        latest[attempt.problem_id] = attempt
    return [latest[problem_id] for problem_id in sorted(latest)]


def recency(attempt: Attempt) -> tuple[datetime, str]:
    return attempt.finished_at, attempt.id


def decides_something(problem: Problem | None, technique: str | None) -> bool:
    if problem is None or len(problem.techniques) < 2:
        return False
    return technique is None or technique in problem.techniques
