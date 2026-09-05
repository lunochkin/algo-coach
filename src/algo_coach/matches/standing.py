from collections.abc import Iterable

from algo_coach.schema import MatchSource, TemplateMatch
from algo_coach.standing import standing

type Pair = tuple[str, str]

# Weakest first, so a stronger writer's verdict overwrites a weaker one's.
BY_WHAT_EACH_KNEW = (MatchSource.CLASSIFIER, MatchSource.GENERATOR, MatchSource.USER)


def standing_matches(matches: Iterable[TemplateMatch]) -> dict[Pair, TemplateMatch]:
    """The verdict that stands on each pair, keyed by template and solution."""
    return standing(
        matches,
        lambda match: (match.template_id, match.solution_id),
        by_what_each_knew=BY_WHAT_EACH_KNEW,
    )
