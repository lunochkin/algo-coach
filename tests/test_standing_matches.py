"""Which verdict stands on a pair.

Ordered by what each writer knew rather than by when it wrote, as a claim
resolves user-first. A matcher runs over a corpus that grows, so latest-wins
would let it overwrite the assertion it audits and the reference it is scored
against.
"""

from datetime import UTC, datetime, timedelta

import pytest

from algo_coach.matches import standing_matches
from algo_coach.schema import MatchSource, TemplateMatch

T0 = datetime(2026, 1, 1, tzinfo=UTC)

PROVENANCE = {
    "model": "a-model",
    "effort": "medium",
    "pin": "a-host",
    "prompt_hash": "0123456789ab",
    "call_id": "call-1",
}


def match(
    source: MatchSource,
    *,
    matched: bool = True,
    at: datetime = T0,
    template_id: str = "t1",
    problem_id: str = "p1",
) -> TemplateMatch:
    fields = {
        "id": f"{source}-{at.isoformat()}-{matched}",
        "created_at": at,
        "template_id": template_id,
        "problem_id": problem_id,
        "matched": matched,
        "source": source,
    }
    if source is MatchSource.CLASSIFIER:
        fields |= PROVENANCE
    return TemplateMatch.model_validate(fields)


def test_nothing_read_stands_for_nothing():
    assert standing_matches([]) == {}


def test_a_lone_verdict_stands():
    reading = match(MatchSource.CLASSIFIER)

    assert standing_matches([reading]) == {("t1", "p1"): reading}


def test_a_hand_annotation_stands_over_both_machine_sources():
    """It is the reference a machine reading is scored against, so nothing a
    machine writes may replace it."""
    annotation = match(MatchSource.USER, matched=True, at=T0)
    asserted = match(MatchSource.GENERATOR, at=T0 + timedelta(days=1))
    read = match(MatchSource.CLASSIFIER, matched=False, at=T0 + timedelta(days=2))

    assert standing_matches([annotation, asserted, read])[("t1", "p1")] is annotation


def test_a_generator_stands_over_a_matcher_reading_the_same_pair():
    """The generator was told the form. The matcher inferred it, and a later
    reading must not supersede the assertion it audits."""
    asserted = match(MatchSource.GENERATOR, at=T0)
    read = match(MatchSource.CLASSIFIER, matched=False, at=T0 + timedelta(days=1))

    assert standing_matches([asserted, read])[("t1", "p1")] is asserted


def test_a_later_matcher_reading_supersedes_an_earlier_one():
    """Within one writer the log's own order decides, since a re-run at a new
    configuration is what supersession is for."""
    first = match(MatchSource.CLASSIFIER, matched=True, at=T0)
    second = match(MatchSource.CLASSIFIER, matched=False, at=T0 + timedelta(days=1))

    assert standing_matches([first, second])[("t1", "p1")] is second


def test_append_order_breaks_a_tie_on_time():
    first = match(MatchSource.CLASSIFIER, matched=True, at=T0)
    second = match(MatchSource.CLASSIFIER, matched=False, at=T0)

    assert standing_matches([first, second])[("t1", "p1")] is second


def test_order_of_reading_does_not_decide():
    """The rule is what each writer knew, so shuffling the log changes
    nothing."""
    annotation = match(MatchSource.USER)
    asserted = match(MatchSource.GENERATOR, at=T0 + timedelta(days=1))
    read = match(MatchSource.CLASSIFIER, at=T0 + timedelta(days=2))

    for order in ([annotation, asserted, read], [read, asserted, annotation]):
        assert standing_matches(order)[("t1", "p1")] is annotation


def test_a_negative_stands_as_readily_as_a_positive():
    """A stored negative is a verdict. Resolution says who answered, never
    what they should have said."""
    annotation = match(MatchSource.USER, matched=False)
    read = match(MatchSource.CLASSIFIER, matched=True, at=T0 + timedelta(days=1))

    assert standing_matches([annotation, read])[("t1", "p1")].matched is False


def test_pairs_resolve_apart():
    """A match asserts one pair. Nothing a verdict says about one template
    reaches another."""
    mine = match(MatchSource.USER, template_id="t1")
    theirs = match(MatchSource.CLASSIFIER, template_id="t2", matched=False)

    standing = standing_matches([mine, theirs])

    assert standing[("t1", "p1")] is mine
    assert standing[("t2", "p1")] is theirs


def test_one_template_over_two_problems_resolves_apart():
    mine = match(MatchSource.CLASSIFIER, problem_id="p1")
    theirs = match(MatchSource.CLASSIFIER, problem_id="p2", matched=False)

    standing = standing_matches([mine, theirs])

    assert (standing[("t1", "p1")], standing[("t1", "p2")]) == (mine, theirs)


@pytest.mark.parametrize("source", MatchSource)
def test_every_writer_can_stand_alone(source):
    """Each is a verdict in its own right. The order decides only where two
    disagree on one pair."""
    only = match(source)

    assert standing_matches([only])[("t1", "p1")] is only
