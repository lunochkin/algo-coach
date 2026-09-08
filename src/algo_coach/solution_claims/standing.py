from collections.abc import Iterable
from operator import attrgetter

from algo_coach.schema import ClaimSource, SolutionClaim
from algo_coach.standing import standing

# Weakest first: the user's claim adjudicates the machine's.
BY_WHAT_EACH_KNEW = (ClaimSource.CLASSIFIER, ClaimSource.USER)


def standing_solution_claims(claims: Iterable[SolutionClaim]) -> dict[str, SolutionClaim]:
    """The claim that stands on each solution: the user's own if any, however
    late the machine's."""
    return standing(claims, attrgetter("solution_id"), by_what_each_knew=BY_WHAT_EACH_KNEW)
