"""A problem, and what produced it.

Generated is the only origin, so unlike a match there is no hand arm to
exempt: provenance is unconditional. A problem written before the field
existed carries none for good, since nothing re-derives a statement, and no
configuration could then be compared over the corpus.
"""

import pytest
from helpers import PROVENANCE
from pydantic import ValidationError

from algo_coach.schema import Problem


def make_problem(**overrides) -> Problem:
    fields = (
        {
            "id": "p1",
            "title": "Two Sum",
            "statement": "Given an array, return ...",
        }
        | PROVENANCE
        | overrides
    )
    return Problem.model_validate(fields)


def test_a_problem_records_what_produced_it():
    """As any machine record does. A generated problem is the product, and one
    whose configuration is unknown cannot be compared with the rest."""
    problem = make_problem()

    assert {field: getattr(problem, field) for field in PROVENANCE} == PROVENANCE


def test_a_problem_without_any_provenance_is_rejected():
    """The whole point of the field. Problems are append-only and identity
    never moves, so one that lands without provenance keeps none."""
    with pytest.raises(ValidationError):
        Problem.model_validate(
            {"id": "p1", "title": "Two Sum", "statement": "Given an array, return ..."}
        )


@pytest.mark.parametrize("missing", PROVENANCE)
def test_a_problem_needs_every_field_that_produced_it(missing):
    """All of them or none, as on a reading: a record whose configuration is
    partly unknown compares with nothing."""
    with pytest.raises(ValidationError, match=missing):
        Problem.model_validate(
            {
                "id": "p1",
                "title": "Two Sum",
                "statement": "Given an array, return ...",
                **{field: value for field, value in PROVENANCE.items() if field != missing},
            }
        )


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
