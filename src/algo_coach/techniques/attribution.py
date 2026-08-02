from collections.abc import Mapping

from algo_coach.schema import Attempt, Problem, TechniqueClaim


def resolve_techniques(
    attempt: Attempt, problem: Problem, claims: Mapping[str, TechniqueClaim]
) -> list[str]:
    """Which techniques an attempt exercised: its claim if one exists,
    otherwise the techniques of the problem it answers.

    `claims` is keyed by attempt id — `latest_by_attempt` over the log.

    Derived on read and never stored, so re-deriving the tag mapping reaches
    every unclaimed attempt. Sorted and deduplicated, as `map_tags` is, so
    grouping does not depend on how a claim ordered its codes.
    """
    claim = claims.get(attempt.id)
    return sorted(set(claim.techniques if claim else problem.techniques))
