from collections.abc import Iterable, Mapping

from algo_coach.schema import Attempt, Problem, TechniqueClaim


def latest_claims(claims: Iterable[TechniqueClaim]) -> Mapping[str, TechniqueClaim]:
    """The claim that stands for each attempt, keyed by attempt id.

    Latest by `created_at`, append order breaking a tie. A later claim
    replaces the whole set rather than merging with the earlier one, so the
    superseded records stay in the log and never reach a reader.
    """
    standing: dict[str, TechniqueClaim] = {}
    for claim in claims:
        current = standing.get(claim.attempt_id)
        if current is None or claim.created_at >= current.created_at:
            standing[claim.attempt_id] = claim
    return standing


def resolve_techniques(
    attempt: Attempt, problem: Problem, claims: Mapping[str, TechniqueClaim]
) -> list[str]:
    """Which techniques an attempt exercised: its claim if one exists,
    otherwise the techniques of the problem it answers.

    Derived on read and never stored, so re-deriving the tag mapping reaches
    every unclaimed attempt. Sorted and deduplicated, as `map_tags` is, so
    grouping does not depend on how a claim ordered its codes.
    """
    claim = claims.get(attempt.id)
    return sorted(set(claim.techniques if claim else problem.techniques))
