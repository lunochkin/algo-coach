from collections.abc import Iterable, Mapping

from algo_coach.log import latest_by_attempt
from algo_coach.schema import Attempt, ClaimSource, Problem, TechniqueClaim


def standing_claims(claims: Iterable[TechniqueClaim]) -> dict[str, TechniqueClaim]:
    """The claim that stands: the user's own if any, however late the machine's."""
    claims = list(claims)
    return latest_by_attempt(claims) | latest_by_attempt(
        [claim for claim in claims if claim.source is ClaimSource.USER]
    )


def resolve_techniques(
    attempt: Attempt, problem: Problem, claims: Mapping[str, TechniqueClaim]
) -> list[str]:
    """The claim's techniques if it names any, otherwise the problem's."""
    claim = claims.get(attempt.id)
    return sorted(set(claim.techniques if claim and claim.techniques else problem.techniques))
