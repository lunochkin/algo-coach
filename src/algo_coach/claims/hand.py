"""A claim the user writes: the drill loop's answer at the moment of solving,
or a hand pass's over the backlog."""

from collections.abc import Sequence

from algo_coach.log import AttemptLog
from algo_coach.mint import user_claim
from algo_coach.schema import Confidence, TechniqueClaim


def claim_by_hand(
    log: AttemptLog,
    attempt_id: str,
    techniques: Sequence[str],
    *,
    confidence: Confidence | None = None,
    informed_by: Sequence[str] = (),
) -> TechniqueClaim:
    """Written whole. Naming nothing declines: the user said the candidates do
    not cover the code, which the schema refuses to take for a lost answer."""
    claim = user_claim(
        attempt_id,
        list(techniques),
        declined=not techniques,
        confidence=confidence,
        informed_by=informed_by,
    )
    log.append_claim(claim)
    return claim


__all__ = ["claim_by_hand"]
