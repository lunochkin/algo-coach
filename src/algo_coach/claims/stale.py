"""Which stored claims this classifier produced, and which a later one replaces.

A machine claim names what produced it, so a re-run can find the ones an
older model or prompt reached, and an eval can find the ones it has already
paid to read. A user's claim names nothing, and nothing re-derives it.
"""

from collections.abc import Iterable

from algo_coach.claims.classifier import Configuration
from algo_coach.log import latest_by_attempt
from algo_coach.schema import ClaimSource, TechniqueClaim


def is_stale(claim: TechniqueClaim, configuration: Configuration) -> bool:
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

    return not at_configuration(claim, configuration)


def at_configuration(claim: TechniqueClaim, configuration: Configuration) -> bool:
    """Whether this classifier produced the claim.

    The positive form of the same comparison. `not is_stale` is not it: it
    means "not known-stale", and a user's claim is at no configuration at all —
    stated here rather than borrowed from the validator that keeps provenance
    off a user's claim.
    """
    if claim.source is not ClaimSource.CLASSIFIER:
        return False
    return (claim.model, claim.effort, claim.prompt_version) == (
        configuration.model,
        configuration.effort,
        configuration.prompt_version,
    )


def readings_at(
    claims: Iterable[TechniqueClaim], configuration: Configuration
) -> dict[str, TechniqueClaim]:
    """The claim this configuration already read each attempt as.

    Filtered before `latest_by_attempt`, never after: running an earlier prompt
    on purpose is a rollback, so an attempt's latest machine claim can be
    another configuration's while this one's reading sits under it.
    """
    return latest_by_attempt([claim for claim in claims if at_configuration(claim, configuration)])
