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
    ask about them.

    Carrying their code, one per problem, on a problem whose tags leave a
    choice to make. Spread across techniques, so a sample cut at any length is
    not carried by whichever technique the backlog holds most of.

    A machine claim does not take an attempt out of the pool. The classifier
    fills what no hand reached, and a user claim is what corrects it. Only the
    user's own answer settles a problem, since asking again would ask what has
    been answered.

    Spread against the claims already made rather than within the batch, since
    the eval set is grown and never redrawn.
    """
    # Claimed drops out after the collapse, not before: filtering first would
    # promote an older attempt and ask the same problem twice.
    collapsed = one_per_problem(eligible(attempts, problems, user_id=user_id, technique=technique))
    answered = [attempt for attempt in collapsed if answered_by_hand(claimed.get(attempt.id))]
    return spread(
        [attempt for attempt in collapsed if not answered_by_hand(claimed.get(attempt.id))],
        problems,
        # What the answered attempts covered, carried past the filter that
        # removed them. They are what the sample joins, so levelling the batch
        # alone would spend it on whatever the eval set already holds most of.
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

    Each step takes an attempt on the technique the order has covered least so
    far, so any prefix of it is spread. A backlog is skewed. A uniform shuffle
    puts most of a thirty-attempt sample on the two or three techniques that
    dominate it, and the score the sample estimates is read per technique.

    An attempt counts toward every technique its problem carries, since a claim
    on it decides all of them. What is levelled is coverage, not how many times
    each technique was drawn from. Shuffled within a technique by `seed`, so a
    sample is described by its seed rather than by listing what it held.

    `covered` is what the order starts from: the techniques a caller has
    already reached, so a code the eval set holds fifteen of waits behind one
    it holds four of. It reorders and never filters. An attempt on a covered
    technique is later, not gone, so a sample cut at any length is still that
    length. Empty by default, which is the levelling a first pass wants.
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
        """The bucket's next attempt nothing has drawn. The cursor never goes
        back, so the scan is paid once per attempt rather than once per step."""
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
