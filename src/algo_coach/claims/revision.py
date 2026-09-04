"""The hand pass run again over what a reading disagrees with."""

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
    """`claimable`'s mirror: what the hand pass has answered, collapsed before
    the filter so a revision asks about the attempt that was scored."""
    collapsed = one_per_problem(eligible(attempts, problems, user_id=user_id, technique=technique))
    return [attempt for attempt in collapsed if answered_by_hand(claimed.get(attempt.id))]


def against(claim: TechniqueClaim, readings: Sequence[Mapping[str, TechniqueClaim]]) -> int:
    """How many of these configurations read the attempt differently, by set
    equality. One that never read it is silent rather than dissenting."""
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
    """The disputed ones, most disputed first. `at_least` draws the line
    between a wrong claim and one wrong configuration. Stable, so ties keep the
    pool's order, which makes two runs of the same review comparable."""
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
