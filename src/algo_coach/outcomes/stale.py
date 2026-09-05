"""Which sites a given configuration has already answered, at a given
question."""

from collections.abc import Iterable

from algo_coach.schema import CallSite, Configuration, SiteOutcome


def answered(
    outcomes: Iterable[SiteOutcome],
    *,
    site: CallSite,
    problem_id: str,
    configuration: Configuration,
    prompt_hash: str,
) -> bool:
    """Whether this site has answered this problem as it would ask now. Any
    record at that text answers, latest or not: a re-run buys the same
    verdict."""
    return any(
        one.site is site
        and one.problem_id == problem_id
        and one.at_configuration(configuration, prompt_hash)
        for one in outcomes
    )
