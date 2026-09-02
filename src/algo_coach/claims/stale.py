"""Which stored claims this classifier produced, and which a later one replaces.

A machine claim names what produced it, so a re-run can find the ones an
older classifier reached, and an eval can find the ones it has already paid to
read. A user's claim names nothing, and nothing re-derives it.
"""

from collections.abc import Iterable, Mapping

from algo_coach.classifier import Configuration
from algo_coach.log import latest_by_attempt
from algo_coach.schema import ClaimSource, TechniqueClaim


def is_stale(claim: TechniqueClaim, configuration: Configuration, prompt_hash: str) -> bool:
    """Whether a claim came from a different question than the one being asked.

    The hash decides, and it is the hash of what *this* attempt would be sent —
    so editing one entry re-derives the attempts carrying that candidate and
    leaves every other one alone. There is no version beside it: a version was
    an author's word for "the reading changed", and a word can be forgotten
    while the text moves. The digest cannot.

    The cost is that a reflowed sentence re-derives the attempts it reaches.
    That is the intended trade — nothing licenses calling an edit cosmetic on
    a model's behalf, and the per-attempt hash keeps the bill to the entries
    actually touched.
    """
    if claim.source is not ClaimSource.CLASSIFIER:
        return False

    return not at_configuration(claim, configuration, prompt_hash)


def at_configuration(claim: TechniqueClaim, configuration: Configuration, prompt_hash: str) -> bool:
    """Whether this classifier, asked this question, produced the claim.

    The positive form of the same comparison. `not is_stale` is not it: it
    means "not known-stale", and a user's claim is at no configuration at all —
    stated here rather than borrowed from the validator that keeps provenance
    off a user's claim.

    The pin and the temperature are compared like the rest: one says which
    weights answered and the other how they were sampled, and a reading from
    another build or another sampler answered a different question. The
    provider that served it is not compared — it is unknown when this is asked,
    and a company name cannot be checked against an endpoint.
    """
    if claim.source is not ClaimSource.CLASSIFIER:
        return False
    return (claim.model, claim.effort, claim.pin, claim.temperature, claim.prompt_hash) == (
        configuration.model,
        configuration.effort,
        configuration.pin,
        configuration.temperature,
        prompt_hash,
    )


def readings_at(
    claims: Iterable[TechniqueClaim],
    configuration: Configuration,
    hashes: Mapping[str, str],
) -> dict[str, TechniqueClaim]:
    """The claim this configuration already read each attempt as, for the
    question it would ask now.

    `hashes` is what each attempt would be sent, keyed by attempt id — an
    attempt missing from it can match nothing, since there is no question to
    compare against.

    Filtered before `latest_by_attempt`, never after: an attempt's latest
    machine claim can be another configuration's, or an older rulebook's, while
    this one's reading sits under it.
    """
    return latest_by_attempt(
        [
            claim
            for claim in claims
            if claim.attempt_id in hashes
            and at_configuration(claim, configuration, hashes[claim.attempt_id])
        ]
    )
