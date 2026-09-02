"""How far the classifier's claims move the board off the fallback.

A sanity check, never a criterion: only the hand claims say a claim is right.
"""

from collections.abc import Iterable, Mapping

from pydantic import BaseModel

from algo_coach.board.view import per_technique
from algo_coach.schema import Attempt, Problem, TechniqueClaim


class TechniqueMovement(BaseModel):
    technique: str
    fallback: int  # attempts credited to it by the problem's techniques alone
    claimed: int  # attempts credited once the claims resolve
    moved: int  # claimed - fallback; negative is credit the claims took away


def movement(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claims: Mapping[str, TechniqueClaim],
) -> list[TechniqueMovement]:
    """The board with the claims against the board without them."""
    attempts = list(attempts)
    fallback = counts(attempts, problems, {})
    claimed = counts(attempts, problems, claims)
    return [
        TechniqueMovement(
            technique=technique,
            fallback=fallback.get(technique, 0),
            claimed=claimed.get(technique, 0),
            moved=claimed.get(technique, 0) - fallback.get(technique, 0),
        )
        for technique in sorted(fallback | claimed)
    ]


def counts(
    attempts: Iterable[Attempt],
    problems: Mapping[str, Problem],
    claims: Mapping[str, TechniqueClaim],
) -> dict[str, int]:
    return {
        row.technique: row.attempt_count for row in per_technique(attempts, problems, claims, {})
    }
