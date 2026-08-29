from collections.abc import Iterable

from algo_coach.schema import MatchSource, TemplateMatch

type Pair = tuple[str, str]

# Weakest first, so a stronger writer's dict overwrites a weaker one's.
BY_WHAT_EACH_KNEW = (MatchSource.CLASSIFIER, MatchSource.GENERATOR, MatchSource.USER)


def latest_by_pair(matches: Iterable[TemplateMatch]) -> dict[Pair, TemplateMatch]:
    """The last verdict on each pair, append order breaking a tie on time.

    Within one writer only. Which writer wins is `standing_matches`, and this
    knows nothing of sources — in what order is the log's question, who wins
    is the record's.
    """
    standing: dict[Pair, TemplateMatch] = {}
    for match in matches:
        pair = (match.template_id, match.problem_id)
        current = standing.get(pair)
        if current is None or match.created_at >= current.created_at:
            standing[pair] = match
    return standing


def standing_matches(matches: Iterable[TemplateMatch]) -> dict[Pair, TemplateMatch]:
    """The verdict that stands on each pair, keyed by template and problem.

    Ordered by what each writer knew rather than by when it wrote. A hand
    annotation stands over both machine sources. A generator's assertion
    stands over a matcher's reading of the same pair, because the generator
    was told the form where the matcher inferred it.

    Latest alone would let the matcher supersede the assertion it audits. It
    runs over a corpus that grows, so it writes far more often than either
    other writer, and a re-run would quietly overwrite the reference it is
    scored against.

    A superseded verdict stays in the log and never reaches a reader, which is
    what makes a matcher's reading safe to store on a pair the generator
    asserted: it is a reading, not a candidate.
    """
    matches = list(matches)
    standing: dict[Pair, TemplateMatch] = {}
    for source in BY_WHAT_EACH_KNEW:
        standing |= latest_by_pair([match for match in matches if match.source is source])
    return standing
