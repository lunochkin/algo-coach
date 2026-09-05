"""Which stored claims a given classifier produced, at a given question."""

from collections.abc import Iterable, Mapping

from algo_coach.calls import Configuration
from algo_coach.log import latest_by_attempt
from algo_coach.schema import ClaimSource, TechniqueClaim


def is_stale(claim: TechniqueClaim, configuration: Configuration, prompt_hash: str) -> bool:
    if claim.source is not ClaimSource.CLASSIFIER:
        return False

    return not at_configuration(claim, configuration, prompt_hash)


def at_configuration(claim: TechniqueClaim, configuration: Configuration, prompt_hash: str) -> bool:
    """Not `not is_stale`: that means "not known-stale", and a user's claim is
    at no configuration at all. The provider is not compared, being unknown
    here."""
    return claim.source is ClaimSource.CLASSIFIER and claim.at_configuration(
        configuration, prompt_hash
    )


def readings_at(
    claims: Iterable[TechniqueClaim],
    configuration: Configuration,
    hashes: Mapping[str, str],
) -> dict[str, TechniqueClaim]:
    """Filtered before `latest_by_attempt`, never after: an attempt's latest
    machine claim can be another configuration's, with this one's under it."""
    return latest_by_attempt(
        [
            claim
            for claim in claims
            if claim.attempt_id in hashes
            and at_configuration(claim, configuration, hashes[claim.attempt_id])
        ]
    )
