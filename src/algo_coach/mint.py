"""Where the engine's identity comes from.

Every stored record carries an id the engine minted and a client never sees.
Kept in one module so the policy is one line to read and one line to change —
a schema model states what a record holds, not where its id came from, and
the clock has no place there either.
"""

import uuid
from datetime import UTC, datetime

from algo_coach.schema import Call, ClaimSource, FailureMode, SelfLabel, TechniqueClaim
from algo_coach.techniques import is_known


def new_id() -> str:
    """Opaque and unguessable: nothing may derive one from a record's content,
    or two engines would mint the same id for different attempts."""
    return uuid.uuid4().hex


def call(
    *,
    model: str,
    effort: str,
    prompt: str,
    prompt_hash: str,
    response: str | None = None,
    error: str | None = None,
    thinking: str | None = None,
    stop_reason: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> Call:
    """One request to a model, minted where every other id is minted."""
    return Call(
        id=new_id(),
        created_at=datetime.now(UTC),
        model=model,
        effort=effort,
        prompt=prompt,
        prompt_hash=prompt_hash,
        response=response,
        error=error,
        thinking=thinking,
        stop_reason=stop_reason,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


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


def classifier_claim(
    attempt_id: str,
    techniques: list[str],
    *,
    model: str,
    effort: str,
    prompt_hash: str,
    call_id: str,
) -> TechniqueClaim:
    """A claim a model made. It names what produced it, since a better
    classifier can recompute it and a user's claim cannot be recomputed at all.

    All four, never a subset: a reading whose configuration is partly unknown
    cannot be compared with one whose configuration is known. The model and
    effort are copied from the call rather than read through it, so the claims
    file says what produced each claim without opening the call log.

    Membership is checked here because this is the only write path that could
    introduce an unrecognised code — every other one draws on the tag mapping,
    which is derived from the vocabulary already. Rejected whole rather than
    per code: a claim asserts one set, and writing the half that passed would
    record a set nobody made.
    """
    unknown = [code for code in techniques if not is_known(code)]
    if unknown:
        raise ValueError(f"unknown technique code(s): {', '.join(unknown)}")
    return TechniqueClaim(
        id=new_id(),
        created_at=datetime.now(UTC),
        attempt_id=attempt_id,
        techniques=techniques,
        source=ClaimSource.CLASSIFIER,
        model=model,
        effort=effort,
        prompt_hash=prompt_hash,
        call_id=call_id,
    )


def self_label(attempt_id: str, mode: FailureMode) -> SelfLabel:
    """Only ever the user's — a machine answering the same question produces a
    `Diagnosis`."""
    return SelfLabel(id=new_id(), created_at=datetime.now(UTC), attempt_id=attempt_id, mode=mode)
