from datetime import UTC, datetime, timedelta

import pytest
from helpers import stored_solution, stored_template

from algo_coach.matches import MatchLog
from algo_coach.schema import MatchSource, TemplateMatch


@pytest.fixture(autouse=True)
def referenced(database):
    """The rows this module's records name by foreign key."""
    stored_template(database, "t1")
    for id in ("s1", "s2", "s3"):
        stored_solution(database, id)


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


def test_append_and_read_back(database):
    log = MatchLog(database)
    match = make_match()
    log.append(match)

    assert log.matches() == [match]


def test_reading_an_empty_store(database):
    assert MatchLog(database).matches() == []


def test_a_later_verdict_appends_rather_than_replacing(database):
    """Append-only: the re-run's answer stands, and what the earlier
    configuration said stays readable."""
    log = MatchLog(database)
    log.append(make_match(id="m1", matched=True))
    log.append(make_match(id="m2", matched=False, created_at=NOW + timedelta(hours=1)))

    assert [match.matched for match in log.matches()] == [True, False]


def test_matches_are_read_in_append_order(database):
    """A tie on `created_at` is broken by what landed last, as it is for the
    records keyed to an attempt."""
    log = MatchLog(database)
    for solution_id in ("s1", "s2", "s3"):
        log.append(make_match(solution_id=solution_id))

    assert [match.solution_id for match in log.matches()] == ["s1", "s2", "s3"]
