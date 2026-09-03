import pytest
from helpers import PROVENANCE, T0
from pydantic import ValidationError

from algo_coach.mint import solution
from algo_coach.schema import Solution, SolutionRole

CODE = "def solve(n):\n    return n\n"


def make_canonical(**overrides) -> Solution:
    fields = (
        {
            "problem_id": "p1",
            "code": CODE,
            "role": SolutionRole.CANONICAL,
        }
        | PROVENANCE
        | overrides
    )
    return solution(**fields)


def test_a_canonical_is_keyed_to_a_problem_and_carries_its_code():
    """It is what a template match reads beside the statement, since which form
    a problem exercises is a question about the solution."""
    canonical = make_canonical()

    assert (canonical.problem_id, canonical.code) == ("p1", CODE)


def test_a_canonical_without_code_is_rejected():
    with pytest.raises(ValidationError, match="code"):
        make_canonical(code="")


def test_a_canonical_names_what_produced_it():
    """A machine record like any other. Nothing re-derives one, but a corpus
    written by two configurations has to say which wrote what."""
    canonical = make_canonical()

    assert {field: getattr(canonical, field) for field in PROVENANCE} == PROVENANCE


@pytest.mark.parametrize("missing", PROVENANCE)
def test_a_canonical_needs_every_field_that_produced_it(missing):
    """All of them or none, as on any reading. Asserted against the model,
    since the minter cannot be called without them at all."""
    kept = {field: value for field, value in PROVENANCE.items() if field != missing}
    with pytest.raises(ValidationError, match=missing):
        Solution.model_validate(
            {
                "id": "s1",
                "created_at": T0,
                "problem_id": "p1",
                "role": SolutionRole.CANONICAL,
                "code": CODE,
            }
            | kept
        )


def test_the_minter_is_what_supplies_provenance():
    """Spelled out at a call site the five fields could be filled partly, and
    a canonical stored that way names a configuration nothing can compare."""
    with pytest.raises(TypeError):
        solution(problem_id="p1", code=CODE, role=SolutionRole.CANONICAL)


def test_a_canonical_says_nothing_about_how_it_ran():
    """Whether it passes is a fact about a run: the cap and the machine decide
    a timeout, and a crash can come from the runner. A `Verification` holds
    that, and the code stays immutable."""
    assert not [
        name
        for name in Solution.model_fields
        if name in {"results", "outcome", "verified", "timeout_ms"}
    ]


def test_a_canonical_is_minted_an_id_and_stamped():
    canonical = make_canonical()

    assert canonical.id != make_canonical().id
    assert canonical.created_at.tzinfo is not None


def test_a_canonical_is_not_an_attempt():
    """It answers no board row and earns no progress. A user who reads one has
    not solved the problem."""
    assert not [name for name in Solution.model_fields if "user" in name]
    assert "attempt_id" not in Solution.model_fields


def test_a_solution_states_which_role_it_was_written_for():
    """Both roles pass the same cases, so passing says nothing about which one
    a solution is. A reader taking a reference for a canonical would teach the
    approach the card exists to replace."""
    reference = make_canonical(role=SolutionRole.REFERENCE)

    assert (make_canonical().role, reference.role) == ("canonical", "reference")


def test_a_solution_without_a_role_is_rejected():
    """No default: a role guessed from the field being absent is the one a
    generation run forgot to state."""
    with pytest.raises(ValidationError, match="role"):
        Solution.model_validate(
            {"id": "s1", "created_at": T0, "problem_id": "p1", "code": CODE} | PROVENANCE
        )
