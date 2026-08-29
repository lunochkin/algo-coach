"""A canonical solution: the code, what produced it, and how each case went.

Exemplary and verified are different properties. A user's solved attempt is
verified and idiosyncratic, a generated solution is exemplary and asserted, and
only one that passes the problem's cases is both.
"""

import pytest
from helpers import PROVENANCE, T0
from pydantic import ValidationError

from algo_coach.mint import canonical_solution
from algo_coach.schema import CanonicalSolution

CODE = "def solve(n):\n    return n\n"


def make_canonical(**overrides) -> CanonicalSolution:
    fields = {"problem_id": "p1", "code": CODE} | PROVENANCE | overrides
    return canonical_solution(**fields)


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
        CanonicalSolution.model_validate(
            {"id": "s1", "created_at": T0, "problem_id": "p1", "code": CODE} | kept
        )


def test_the_minter_is_what_supplies_provenance():
    """Spelled out at a call site the five fields could be filled partly, and
    a canonical stored that way names a configuration nothing can compare."""
    with pytest.raises(TypeError):
        canonical_solution(problem_id="p1", code=CODE)


def test_a_canonical_says_nothing_about_how_it_ran():
    """Whether it passes is a fact about a run: the cap and the machine decide
    a timeout, and a crash can come from the runner. A `Verification` holds
    that, and the code stays immutable."""
    assert not [
        name
        for name in CanonicalSolution.model_fields
        if name in {"results", "outcome", "verified", "timeout_ms"}
    ]


def test_a_canonical_is_minted_an_id_and_stamped():
    canonical = make_canonical()

    assert canonical.id != make_canonical().id
    assert canonical.created_at.tzinfo is not None


def test_a_canonical_is_not_an_attempt():
    """It answers no board row and earns no progress. A user who reads one has
    not solved the problem."""
    assert not [name for name in CanonicalSolution.model_fields if "user" in name]
    assert "attempt_id" not in CanonicalSolution.model_fields
