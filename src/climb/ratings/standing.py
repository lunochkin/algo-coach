from collections.abc import Iterable
from operator import attrgetter

from climb.schema import ClaimSource, DifficultyRating, Problem
from climb.standing import standing

# weakest first: the user's rating stands over the machine's, however late
BY_WHAT_EACH_KNEW = (ClaimSource.CLASSIFIER, ClaimSource.USER)


def with_standing_difficulty(
    problems: Iterable[Problem], ratings: Iterable[DifficultyRating]
) -> list[Problem]:
    """Each problem carrying its standing difficulty; the generator's label
    where no rating exists."""
    stands = standing(ratings, attrgetter("problem_id"), by_what_each_knew=BY_WHAT_EACH_KNEW)
    return [
        problem.model_copy(update={"difficulty": stands[problem.id].difficulty})
        if problem.id in stands
        else problem
        for problem in problems
    ]
