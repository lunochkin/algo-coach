"""Which stored claims a later classifier should replace.

A machine claim names what produced it, so a re-run can find the ones an
older model or prompt reached. A user's claim names nothing, and nothing
re-derives it.
"""

from algo_coach.schema import ClaimSource, TechniqueClaim


def is_stale(claim: TechniqueClaim, *, model: str, effort: str, prompt_version: str) -> bool:
    """Whether a claim came from a different classifier than the one running.

    Compared whole rather than ordered: a version is an identity, not a number
    to be greater than, so running an earlier prompt on purpose re-derives what
    a later one wrote and a rollback needs no separate path.

    The prompt hash is deliberately absent. The version is the author's
    statement that the reading changed meaningfully and is what marks a stored
    claim stale; the hash is the mechanical fact of the text and marks nothing.
    Driving staleness from it would re-derive the backlog for a reflowed
    sentence — the hash is a syntactic boundary, the version a semantic one,
    and only the semantic one should cost money.
    """
    if claim.source is not ClaimSource.CLASSIFIER:
        return False
    return (claim.model, claim.effort, claim.prompt_version) != (model, effort, prompt_version)
