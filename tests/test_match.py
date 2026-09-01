"""A template match: one template against one solution, and what came back.

Not a claim about an attempt — a fact about the corpus — so it shares the
provenance rules and nothing else.
"""

from datetime import UTC, datetime

import pytest
from helpers import PROVENANCE
from pydantic import ValidationError

from algo_coach.mint import generator_match
from algo_coach.schema import MatchSource, TemplateMatch


def make_match(source: MatchSource, **overrides) -> TemplateMatch:
    fields = {
        "id": "m1",
        "created_at": datetime.now(UTC),
        "template_id": "t1",
        "solution_id": "s1",
        "matched": True,
        "source": source,
    } | overrides
    return TemplateMatch.model_validate(fields)


def test_a_match_is_one_template_against_one_problem():
    """Not a set per template: problems arrive one at a time, and a set record
    would rewrite pairs already settled whenever the corpus grew."""
    match = make_match(MatchSource.USER)

    assert (match.template_id, match.solution_id) == ("t1", "s1")
    assert not [name for name in TemplateMatch.model_fields if name.endswith("_ids")]


def test_a_negative_is_a_verdict_and_is_stored():
    """Or every re-run re-tests every non-match forever."""
    assert make_match(MatchSource.USER, matched=False).matched is False


def test_an_annotation_is_blind_unless_it_says_otherwise():
    """The first pass is asked from the statement and the cues alone, so an
    empty list is what a record means when nothing recorded what its author
    saw."""
    assert make_match(MatchSource.USER).informed_by == []


def test_a_hand_match_records_the_verdicts_its_author_saw():
    """Not provenance: provenance is what produced a reading, this is what its
    author had in view. A hand record carries the second and never the
    first."""
    match = make_match(MatchSource.USER, informed_by=["call-1", "call-2"])

    assert match.informed_by == ["call-1", "call-2"]
    assert [field for field in match.RECORDED if getattr(match, field) is not None] == []


def test_verdicts_are_named_one_by_one_rather_than_flagged():
    """An annotation made after seeing one matcher's verdict is still
    independent of another's, and configurations are scored against the same
    records."""
    match = make_match(MatchSource.USER, informed_by=["call-1"])

    assert "call-1" in match.informed_by
    assert "call-2" not in match.informed_by


def test_a_match_states_its_verdict():
    with pytest.raises(ValidationError):
        make_match(MatchSource.CLASSIFIER, matched=None, **PROVENANCE)


def test_a_match_records_its_source():
    """Which of the two readers answered — the same question a claim's source
    answers, since one is scored against the other."""
    with pytest.raises(ValidationError, match="source"):
        TemplateMatch.model_validate(
            {
                "id": "m1",
                "created_at": datetime.now(UTC),
                "template_id": "t1",
                "solution_id": "s1",
                "matched": True,
            }
        )


def test_a_machine_match_records_what_produced_it():
    """Provenance as a claim carries it: re-deriving has to find the stale
    readings and leave the hand ones alone."""
    match = make_match(MatchSource.CLASSIFIER, **PROVENANCE)

    assert {field: getattr(match, field) for field in PROVENANCE} == PROVENANCE


def test_a_machine_match_without_any_provenance_is_rejected():
    with pytest.raises(ValidationError):
        make_match(MatchSource.CLASSIFIER)


@pytest.mark.parametrize("missing", PROVENANCE)
def test_a_machine_match_needs_every_field_that_produced_it(missing):
    """All of them or none: a reading whose configuration is partly unknown
    compares with nothing."""
    with pytest.raises(ValidationError, match=missing):
        make_match(
            MatchSource.CLASSIFIER,
            **{field: value for field, value in PROVENANCE.items() if field != missing},
        )


@pytest.mark.parametrize("field", [*PROVENANCE, "temperature", "provider"])
def test_a_hand_match_carries_no_provenance(field):
    """Nothing re-derives a hand match, so naming a model would name one that
    never touched it."""
    value = 0.0 if field == "temperature" else PROVENANCE.get(field, "a-company")
    with pytest.raises(ValidationError, match=field):
        make_match(MatchSource.USER, **{field: value})


def test_a_machine_match_is_greedy_and_says_so():
    """`None` is the provider's own default rather than a gap — a named arm,
    as it is on a claim."""
    greedy = make_match(MatchSource.CLASSIFIER, temperature=0.0, **PROVENANCE)

    assert greedy.temperature == 0.0
    assert make_match(MatchSource.CLASSIFIER, **PROVENANCE).temperature is None


def test_who_served_a_machine_match_is_recorded():
    """Recorded and never compared: the router names a company, and a company
    serves several builds of a model."""
    assert make_match(MatchSource.CLASSIFIER, provider="a-company", **PROVENANCE).provider == (
        "a-company"
    )


def test_a_match_is_keyed_to_no_attempt():
    """A fact about the corpus, not about a sitting. Nothing to key to an
    attempt, and the ladder it feeds is read long before one exists."""
    assert "attempt_id" not in TemplateMatch.model_fields


def test_a_match_names_no_card():
    """The template is the pair's half. A card is recoverable from it, and a
    copy taken here would be a second place to be wrong."""
    assert not [name for name in TemplateMatch.model_fields if "card" in name]


def test_the_canonical_a_problem_was_generated_with_asserts_its_own_match():
    """Its brief said which template, so the pair is provenance rather than a
    reading and nothing pays a call to learn it."""
    match = generator_match("t1", "s1")

    assert (match.template_id, match.solution_id) == ("t1", "s1")
    assert match.source is MatchSource.GENERATOR


def test_a_generator_match_carries_no_configuration():
    """Nothing re-derives it, and the solution it points at already names the
    call that wrote it."""
    match = generator_match("t1", "s1")

    assert [field for field in match.RECORDED if getattr(match, field) is not None] == []


def test_a_generator_only_ever_asserts_a_positive():
    """It asserts the form it was briefed on and says nothing about the
    templates it was not, which is the matcher's question."""
    assert generator_match("t1", "s1").matched is True


def test_a_generator_match_has_seen_nothing():
    """The brief named a template. No reading of the pair was in view, and
    none could have been before the solution existed."""
    assert generator_match("t1", "s1").informed_by == []


def test_the_three_writers_are_named_apart():
    """A hand annotation stands over both machine sources, and a generator's
    assertion stands over a matcher's reading of the same pair."""
    assert set(MatchSource) == {
        MatchSource.USER,
        MatchSource.GENERATOR,
        MatchSource.CLASSIFIER,
    }
