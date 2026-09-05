from collections.abc import Iterable

from algo_coach.schema import MatchSource, TemplateMatch
from algo_coach.standing import latest_by, standing

type Pair = tuple[str, str]

# Weakest first, so a stronger writer's verdict overwrites a weaker one's.
BY_WHAT_EACH_KNEW = (MatchSource.CLASSIFIER, MatchSource.GENERATOR, MatchSource.USER)


def latest_readings(matches: Iterable[TemplateMatch]) -> dict[Pair, TemplateMatch]:
    """The latest machine reading per pair, from any configuration: what a
    reader is shown, never what is scored or stands."""
    return latest_by(
        (match for match in matches if match.source is MatchSource.CLASSIFIER),
        lambda match: (match.template_id, match.solution_id),
    )


def standing_matches(matches: Iterable[TemplateMatch]) -> dict[Pair, TemplateMatch]:
    """The verdict that stands on each pair, keyed by template and solution."""
    return standing(
        matches,
        lambda match: (match.template_id, match.solution_id),
        by_what_each_knew=BY_WHAT_EACH_KNEW,
    )
