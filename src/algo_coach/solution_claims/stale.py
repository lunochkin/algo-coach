"""Which stored claims a given classifier produced, at a given question."""

from collections.abc import Iterable, Mapping, Sequence

from algo_coach.schema import ClaimSource, Configuration, Solution, SolutionClaim


def at_configuration(claim: SolutionClaim, configuration: Configuration, prompt_hash: str) -> bool:
    """Whether this classifier, asked this question, produced the record. The
    provider that served it is recorded and never compared, and a user claim
    is at no configuration at all."""
    return claim.source is ClaimSource.CLASSIFIER and claim.at_configuration(
        configuration, prompt_hash
    )


def outstanding(
    solutions: Sequence[Solution],
    claims: Iterable[SolutionClaim],
    hashes: Mapping[str, str],
    *,
    configuration: Configuration,
) -> list[Solution]:
    """The solutions this configuration has not read as it would ask now.
    `hashes` is what each would be sent, keyed by solution. Any record at that
    text answers, latest or not: a re-run buys the same verdict."""
    read = {
        claim.solution_id
        for claim in claims
        if claim.solution_id in hashes
        and at_configuration(claim, configuration, hashes[claim.solution_id])
    }
    return [solution for solution in solutions if solution.id not in read]
