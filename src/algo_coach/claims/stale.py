"""Which stored claims a later classifier should replace.

A machine claim names what produced it, so a re-run can find the ones an
older model or prompt reached. A user's claim names nothing, and nothing
re-derives it.
"""

from algo_coach.schema import ClaimSource, TechniqueClaim


def is_stale(claim: TechniqueClaim, *, model: str, prompt_version: str) -> bool:
    """Whether a claim came from a different classifier than the one running.

    Compared whole rather than ordered: a version is an identity, not a number
    to be greater than, so running an earlier prompt on purpose re-derives what
    a later one wrote and a rollback needs no separate path.
    """
    if claim.source is not ClaimSource.CLASSIFIER:
        return False
    return (claim.model, claim.prompt_version) != (model, prompt_version)
