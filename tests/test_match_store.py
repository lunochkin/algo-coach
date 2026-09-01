"""The match log: append-only, like the attempt log and for the same reason —
a verdict re-read is a verdict paid for twice.
"""

from datetime import UTC, datetime, timedelta

from algo_coach.matches import MatchLog
from algo_coach.schema import MatchSource, TemplateMatch

NOW = datetime.now(UTC)


def make_match(template_id: str = "t1", solution_id: str = "s1", **overrides) -> TemplateMatch:
    fields = {
        "id": f"m-{template_id}-{solution_id}",
        "created_at": NOW,
        "template_id": template_id,
        "solution_id": solution_id,
        "matched": True,
        "source": MatchSource.USER,
    } | overrides
    return TemplateMatch.model_validate(fields)


def test_append_and_read_back(tmp_path):
    log = MatchLog(tmp_path)
    match = make_match()
    log.append(match)

    assert log.matches() == [match]


def test_reading_an_empty_store(tmp_path):
    assert MatchLog(tmp_path).matches() == []


def test_a_later_verdict_appends_rather_than_replacing(tmp_path):
    """Append-only: the re-run's answer stands, and what the earlier
    configuration said stays readable."""
    log = MatchLog(tmp_path)
    log.append(make_match(id="m1", matched=True))
    log.append(make_match(id="m2", matched=False, created_at=NOW + timedelta(hours=1)))

    assert [match.matched for match in log.matches()] == [True, False]


def test_matches_are_read_in_append_order(tmp_path):
    """A tie on `created_at` is broken by what landed last, as it is for the
    records keyed to an attempt."""
    log = MatchLog(tmp_path)
    for solution_id in ("s1", "s2", "s3"):
        log.append(make_match(solution_id=solution_id))

    assert [match.solution_id for match in log.matches()] == ["s1", "s2", "s3"]
