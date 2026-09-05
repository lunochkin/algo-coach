from collections.abc import Iterable, Mapping
from operator import attrgetter

from algo_coach.schema import Attempt, ClaimSource, Problem, TechniqueClaim
from algo_coach.standing import standing

# Weakest first: the user's claim stands over the machine's.
BY_WHAT_EACH_KNEW = (ClaimSource.CLASSIFIER, ClaimSource.USER)


def standing_claims(claims: Iterable[TechniqueClaim]) -> dict[str, TechniqueClaim]:
    """The claim that stands: the user's own if any, however late the
    machine's."""
    return standing(claims, attrgetter("attempt_id"), by_what_each_knew=BY_WHAT_EACH_KNEW)


def resolve_techniques(
    attempt: Attempt, problem: Problem, claims: Mapping[str, TechniqueClaim]
) -> list[str]:
    """The claim's techniques if it names any, otherwise the problem's."""
    claim = claims.get(attempt.id)
    return sorted(set(claim.techniques if claim and claim.techniques else problem.techniques))
