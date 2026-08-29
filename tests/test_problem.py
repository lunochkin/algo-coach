"""A problem, what produced it, and what it was written for.

Generated is the only origin, so unlike a match there is no hand arm to
exempt: provenance is unconditional. A problem written before the field
existed carries none for good, since nothing re-derives a statement, and no
configuration could then be compared over the corpus.
"""

import pytest
from helpers import GENERATED, PROVENANCE
from pydantic import ValidationError

from algo_coach.schema import Problem

CONTENT = {
    "id": "p1",
    "title": "Two Sum",
    "statement": "Given an array, return ...",
}


def make_problem(**overrides) -> Problem:
    return Problem.model_validate(CONTENT | GENERATED | overrides)


def test_a_problem_records_what_produced_it():
    """As any machine record does. A generated problem is the product, and one
    whose configuration is unknown cannot be compared with the rest."""
    problem = make_problem()

    assert {field: getattr(problem, field) for field in PROVENANCE} == PROVENANCE


def test_a_problem_without_any_provenance_is_rejected():
    """The whole point of the field. Problems are append-only and identity
    never moves, so one that lands without provenance keeps none."""
    with pytest.raises(ValidationError):
        Problem.model_validate(CONTENT | {"generated_for": "t1"})


@pytest.mark.parametrize("missing", PROVENANCE)
def test_a_problem_needs_every_field_that_produced_it(missing):
    """All of them or none, as on a reading: a record whose configuration is
    partly unknown compares with nothing."""
    kept = {field: value for field, value in GENERATED.items() if field != missing}
    with pytest.raises(ValidationError, match=missing):
        Problem.model_validate(CONTENT | kept)


def test_a_problem_has_no_hand_arm():
    """A match is written by two readers and its validator branches on which.
    A problem has one origin, so nothing exempts it from provenance and there
    is no source to branch on."""
    assert "source" not in Problem.model_fields


def test_generation_is_sampled_and_says_so():
    """The exception the provenance rule names. A reading is greedy so a
    verdict is not resampled; generation wants the variance, or one model's
    habits become the whole corpus."""
    sampled = make_problem(temperature=1.0)

    assert sampled.temperature == 1.0
    assert make_problem().temperature is None


def test_who_served_a_problem_is_recorded():
    """Recorded and never compared, as on a reading: the router names a
    company, and a company serves several builds of a model."""
    assert make_problem(provider="a-company").provider == "a-company"


def test_what_a_problem_cost_is_recorded_rather_than_required():
    """A price is a fact about when a problem was written, not about which
    model wrote it, so two problems compare whether or not either carries
    one."""
    assert make_problem().cost is None
    assert make_problem(cost=0.02).cost == 0.02


def test_a_problem_names_the_template_it_was_written_for():
    """An assertion rather than a reading: the generator was told the form,
    where a matcher infers it. That is what makes the first `TemplateMatch` on
    the pair provenance."""
    assert make_problem(generated_for="t7").generated_for == "t7"


def test_a_problem_written_for_no_template_is_rejected():
    """The engine writes a problem for one of a card's templates, so there is
    no arm where the brief named none."""
    with pytest.raises(ValidationError, match="generated_for"):
        Problem.model_validate(CONTENT | PROVENANCE)


def test_a_blank_template_is_rejected_too():
    """It passes a presence check while naming nothing."""
    with pytest.raises(ValidationError, match="generated_for"):
        make_problem(generated_for="")


def test_one_template_is_named_rather_than_a_set():
    """It says what the problem was written for, never what it exercises. The
    templates it also matches are the matcher's question, and they are
    `TemplateMatch` records rather than a field here."""
    assert isinstance(make_problem().generated_for, str)
