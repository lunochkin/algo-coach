"""Where the engine's identity comes from.

Every stored record carries an id the engine minted and a client never sees.
Kept in one module so the policy is one line to read and one line to change —
a schema model states what a record holds, not where its id came from, and
the clock has no place there either.
"""

import uuid
from datetime import UTC, datetime

from algo_coach.schema import ClaimSource, FailureMode, SelfLabel, TechniqueClaim


def new_id() -> str:
    """Opaque and unguessable: nothing may derive one from a record's content,
    or two engines would mint the same id for different attempts."""
    return uuid.uuid4().hex


def user_claim(attempt_id: str, techniques: list[str]) -> TechniqueClaim:
    """A claim the user made, in the drill loop or over the stored log. It
    carries no model or prompt version because nothing re-derives it."""
    return TechniqueClaim(
        id=new_id(),
        created_at=datetime.now(UTC),
        attempt_id=attempt_id,
        techniques=techniques,
        source=ClaimSource.USER,
    )


def self_label(attempt_id: str, mode: FailureMode) -> SelfLabel:
    """Only ever the user's — a machine answering the same question produces a
    `Diagnosis`."""
    return SelfLabel(id=new_id(), created_at=datetime.now(UTC), attempt_id=attempt_id, mode=mode)
