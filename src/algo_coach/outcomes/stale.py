"""Which sites a given configuration has already answered, at a given question."""

from collections.abc import Iterable

from algo_coach.calls import Configuration
from algo_coach.schema import CallSite, SiteOutcome


def at_configuration(outcome: SiteOutcome, configuration: Configuration, prompt_hash: str) -> bool:
    """Whether this configuration, asked this question, produced the record.
    The provider that served it is recorded and never compared."""
    return (
        outcome.model,
        outcome.effort,
        outcome.pin,
        outcome.temperature,
        outcome.prompt_hash,
    ) == (
        configuration.model,
        configuration.effort,
        configuration.pin,
        configuration.temperature,
        prompt_hash,
    )


def answered(
    outcomes: Iterable[SiteOutcome],
    *,
    site: CallSite,
    problem_id: str,
    configuration: Configuration,
    prompt_hash: str,
) -> bool:
    """Whether this site has answered this problem as it would ask now. Any
    record at that text answers, latest or not: a re-run buys the same verdict."""
    return any(
        one.site is site
        and one.problem_id == problem_id
        and at_configuration(one, configuration, prompt_hash)
        for one in outcomes
    )
