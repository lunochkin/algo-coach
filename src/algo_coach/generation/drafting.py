"""Moving a draft between the states of the writing. The store is working
state, so a draft is revised in place, and it moves forward only."""

from typing import Any

from algo_coach.drafts import DraftStore
from algo_coach.generation.checks import (
    Discard,
)
from algo_coach.generation.resuming import later
from algo_coach.schema import (
    Draft,
    WritingState,
)


def advanced(drafts: DraftStore | None, draft: Draft, state: WritingState, **fields: Any) -> Draft:
    """Forward only: a resume takes the local steps before the one it starts
    at, and a draft moved back would re-pay the calls it already holds if the
    run then died."""
    return held(drafts, moved(draft, later(draft.state, state), **fields))


def rejected(drafts: DraftStore | None, draft: Draft, gate: Discard | None) -> Draft:
    """A gate the run reached, as against the hand exit `reject` writes."""
    return held(drafts, moved(draft, WritingState.REJECTED, gate=gate))


def held(drafts: DraftStore | None, draft: Draft) -> Draft:
    """Written after every step that moved it, so a run that dies leaves the
    draft where it stopped. Silent without a store, as `Writing` is."""
    if drafts is not None:
        drafts.put(draft)
    return draft


def cleared(drafts: DraftStore | None, draft: Draft) -> None:
    """The draft is working state, and the problem it became is what a reader
    finds. Nothing in it is re-derivable from anywhere else, so clearing it is
    what landing means."""
    if drafts is not None:
        drafts.remove(draft.id)


def swept(drafts: DraftStore | None) -> None:
    """A draft naming a problem landed and was not cleared, so the run that
    wrote it died between the two. Cleared here, since writing the problem
    again is the only other way to finish it."""
    if drafts is None:
        return
    for draft in drafts.all():
        if draft.state is WritingState.LANDED:
            drafts.remove(draft.id)


def moved(draft: Draft, state: WritingState, **fields: Any) -> Draft:
    """Revised in place rather than appended: the draft store is working state,
    and a step's answer moves the draft it was written on."""
    return Draft.model_validate(draft.model_dump() | {"state": state} | fields)


def reject(drafts: DraftStore | None, draft: Draft, gate: Discard = Discard.UNEXERCISED) -> Draft:
    """The exit a held draft takes where no resume would separate it: the
    reference wrote the form, so the claim holds and this problem does not
    exercise it. Read by hand, since the run cannot tell that answer from an
    input generator that built the wrong shape.

    A landed draft is not rejected. It names a problem a reader already finds,
    and clearing it is what landing means, so one still in the store is a
    crash's leftover rather than a writing to reject.
    """
    if draft.state in (WritingState.LANDED, WritingState.REJECTED):
        raise ValueError(f"a {draft.state} draft is not rejected")
    return held(drafts, moved(draft, WritingState.REJECTED, gate=gate))


__all__ = [
    "advanced",
    "cleared",
    "held",
    "moved",
    "reject",
    "rejected",
    "swept",
]
