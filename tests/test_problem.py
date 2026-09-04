import pytest
from helpers import GENERATED, PROVENANCE
from pydantic import ValidationError

from algo_coach.schema import Problem, ProblemStatus, RetirementReason

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


def test_a_problem_written_from_a_technique_brief_names_no_template():
    """A template is the tightest brief and a technique a looser one. Nothing
    told this generator a form, so nothing may assert a pair."""
    assert Problem.model_validate(CONTENT | PROVENANCE).generated_for is None


def test_a_blank_template_is_rejected():
    """It passes a presence check while naming nothing. Absent is the arm for
    a brief that named no form."""
    with pytest.raises(ValidationError, match="generated_for"):
        make_problem(generated_for="")


def test_one_template_is_named_rather_than_a_set():
    """It says what the problem was written for, never what it exercises. The
    templates it also matches are the matcher's question, and they are
    `TemplateMatch` records rather than a field here."""
    assert isinstance(make_problem().generated_for, str)


def test_a_problem_starts_created_rather_than_served():
    """Written and verified is not cleared to serve. What promotes it is the
    quality bars, which do not exist yet."""
    problem = make_problem()

    assert problem.status is ProblemStatus.CREATED
    assert problem.retired_reason is None


def test_a_problem_is_retired_for_a_named_reason():
    """Named rather than flagged: only a defective problem's attempts are
    excluded, and a bare status would make every reader guess which
    happened."""
    for reason in RetirementReason:
        problem = make_problem(status="retired", retired_reason=reason)

        assert problem.retired_reason is reason


def test_the_reasons_are_the_two_the_board_reads_apart():
    """A defective problem was never a fair test. A telegraphed one asked what
    its cases decide, so its attempts stay evidence."""
    assert set(RetirementReason) == {
        RetirementReason.DEFECTIVE,
        RetirementReason.TELEGRAPHED,
    }


def test_a_retired_problem_must_say_why():
    """Whether its attempts count is read off the reason, so a retirement
    without one would be excluded or counted by whichever reader guessed."""
    with pytest.raises(ValidationError, match="retired_reason"):
        make_problem(status="retired")


@pytest.mark.parametrize("status", [ProblemStatus.CREATED, ProblemStatus.ACTIVE])
def test_a_problem_still_in_service_carries_no_reason(status):
    """It would name a retirement that did not happen."""
    with pytest.raises(ValidationError, match="retired_reason"):
        make_problem(status=status, retired_reason="defective")


def test_an_unnamed_status_is_rejected():
    with pytest.raises(ValidationError, match="status"):
        make_problem(status="broken")


def test_an_unnamed_reason_is_rejected():
    with pytest.raises(ValidationError, match="retired_reason"):
        make_problem(status="retired", retired_reason="wrong")
