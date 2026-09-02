from collections.abc import Iterable

from algo_coach.schema import MatchSource, TemplateMatch

type Pair = tuple[str, str]

# Weakest first, so a stronger writer's dict overwrites a weaker one's.
BY_WHAT_EACH_KNEW = (MatchSource.CLASSIFIER, MatchSource.GENERATOR, MatchSource.USER)


def latest_by_pair(matches: Iterable[TemplateMatch]) -> dict[Pair, TemplateMatch]:
    """The last verdict on each pair, append order breaking a tie on time.
    Within one writer only; which writer wins is `standing_matches`."""
    standing: dict[Pair, TemplateMatch] = {}
    for match in matches:
        pair = (match.template_id, match.solution_id)
        current = standing.get(pair)
        if current is None or match.created_at >= current.created_at:
            standing[pair] = match
    return standing


def standing_matches(matches: Iterable[TemplateMatch]) -> dict[Pair, TemplateMatch]:
    """The verdict that stands on each pair, keyed by template and solution."""
    matches = list(matches)
    standing: dict[Pair, TemplateMatch] = {}
    for source in BY_WHAT_EACH_KNEW:
        standing |= latest_by_pair([match for match in matches if match.source is source])
    return standing
