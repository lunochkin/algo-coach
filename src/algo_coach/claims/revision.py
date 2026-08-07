"""The hand pass run a second time, over what it already answered.

A claim is open to revision — that is why it is its own record rather than a
field on the attempt. What makes a revision worth asking for is a reading that
disagrees with it: the hand claims are ground truth by construction, not by
being right, and a disagreement is the only place a mislabelled one surfaces.

Which attempts to revisit is a question about the log, not about the terminal,
so it is answered here. What the user is shown while deciding is the adapter's.
"""

from collections.abc import Iterable, Mapping, Sequence

from algo_coach.claims.sample import answered_by_hand, eligible, one_per_problem
from algo_coach.schema import Attempt, Problem, TechniqueClaim


def revisable(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claimed: Mapping[str, TechniqueClaim],
    *,
    user_id: str,
    technique: str | None = None,
) -> list[Attempt]:
    """The attempts a revision could change — `claimable`'s mirror.

    Same pool, same collapse, the opposite filter: what the hand pass has
    already answered rather than what it has not. Collapsed before the filter
    for the same reason, so a revision asks about the attempt that was scored.
    """
    collapsed = one_per_problem(eligible(attempts, problems, user_id=user_id, technique=technique))
    return [attempt for attempt in collapsed if answered_by_hand(claimed.get(attempt.id))]


def against(claim: TechniqueClaim, readings: Sequence[Mapping[str, TechniqueClaim]]) -> int:
    """How many of these configurations read the attempt differently.

    Set equality, as the score uses: a reading naming a subset of the claim
    disagrees with it exactly as one naming something else does. A
    configuration that never read the attempt is not a dissenter and is not
    counted — it is silent, which is a third thing.
    """
    wanted = set(claim.techniques)
    return sum(
        1
        for stored in readings
        if (reading := stored.get(claim.attempt_id)) is not None
        and set(reading.techniques) != wanted
    )


def contested(
    attempts: Sequence[Attempt],
    standing: Mapping[str, TechniqueClaim],
    readings: Sequence[Mapping[str, TechniqueClaim]],
    *,
    at_least: int = 1,
) -> list[Attempt]:
    """The disputed ones, most disputed first.

    Every configuration disagreeing says either the claim is wrong or the
    vocabulary is ambiguous, and both are worth an answer; one configuration
    disagreeing usually says that configuration is wrong. Ordering by the count
    puts the attempts that decide something first, and `at_least` is where a
    reader draws the line between the two.

    Stable, so attempts tied on the count keep the pool's order — by problem,
    which is what makes two runs of the same review comparable.
    """
    counted = [
        (attempt, against(standing[attempt.id], readings))
        for attempt in attempts
        if attempt.id in standing
    ]
    return [
        attempt
        for attempt, count in sorted(counted, key=lambda pair: -pair[1])
        if count >= at_least
    ]
