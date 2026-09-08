from datetime import UTC, datetime

import pytest
from helpers import PROVENANCE_FIELDS
from pydantic import ValidationError

from algo_coach.mint import machine_solution_claim, user_solution_claim
from algo_coach.schema import AttemptClaim, ClaimSource, MachineProvenance, SolutionClaim


def make_solution_claim(source: ClaimSource, **overrides) -> SolutionClaim:
    fields = {
        "id": "r1",
        "created_at": datetime.now(UTC),
        "solution_id": "s1",
        "techniques": ["sliding-window"],
        "source": source,
    } | overrides
    return SolutionClaim.model_validate(fields)


def test_a_reading_is_keyed_to_a_solution():
    """A technique is displayed by code, so the subject is the solution rather
    than the problem it answers."""
    assert make_solution_claim(ClaimSource.USER).solution_id == "s1"
    assert "attempt_id" not in SolutionClaim.model_fields


def test_a_solution_naming_nothing_is_rejected():
    """It passes a presence check while pointing at no code."""
    with pytest.raises(ValidationError, match="solution_id"):
        make_solution_claim(ClaimSource.USER, solution_id="")


def test_one_record_names_every_technique_of_one_solution():
    """Asserted together, so a later claim replaces the whole set rather
    than merging with it."""
    claim = make_solution_claim(ClaimSource.USER, techniques=["sliding-window", "two-pointers"])

    assert claim.techniques == ["sliding-window", "two-pointers"]


def test_an_empty_reading_is_a_verdict_rather_than_an_absence():
    """A claim is only ever written deliberately, so naming nothing says the
    vocabulary does not cover this code."""
    assert (
        make_solution_claim(ClaimSource.CLASSIFIER, techniques=[], **PROVENANCE_FIELDS).techniques
        == []
    )


def test_a_reading_needs_no_decline():
    """A claim needs one because the drill loop records nothing where the user
    skips, which makes an empty claim ambiguous. Nothing skips here."""
    assert "declined" in AttemptClaim.model_fields
    assert "declined" not in SolutionClaim.model_fields


def test_a_machine_reading_carries_its_whole_configuration():
    """One whose configuration is partly known compares with nothing."""
    with pytest.raises(ValidationError, match="machine record needs"):
        make_solution_claim(ClaimSource.CLASSIFIER)

    assert make_solution_claim(ClaimSource.CLASSIFIER, **PROVENANCE_FIELDS).model == "a-model"


def test_a_hand_reading_carries_none_of_it():
    """Nothing re-derives it, so any of it would name a configuration that
    never touched the record."""
    with pytest.raises(ValidationError, match="user record carries no"):
        make_solution_claim(ClaimSource.USER, **PROVENANCE_FIELDS)


def test_a_reading_records_what_its_author_saw():
    """Named one by one, so a record made after seeing one configuration is
    still independent of another."""
    assert make_solution_claim(ClaimSource.USER).informed_by == []
    assert make_solution_claim(ClaimSource.USER, informed_by=["call-1"]).informed_by == ["call-1"]


def test_the_two_writers_are_named_apart():
    """The user's stands over any machine claim however late, as a claim
    resolves."""
    assert set(ClaimSource) == {ClaimSource.USER, ClaimSource.CLASSIFIER}


def test_a_hand_reading_is_minted_blind_and_unconfigured():
    claim = user_solution_claim("s1", ["sliding-window"])

    assert (claim.source, claim.solution_id) == (ClaimSource.USER, "s1")
    assert [field for field in claim.RECORDED if getattr(claim, field) is not None] == []
    assert claim.informed_by == []


def test_a_machine_reading_names_what_produced_it():
    """The prompt hash is what makes it stale, so editing one criterion re-reads
    the solutions that criterion reached."""
    claim = machine_solution_claim(
        "s1",
        ["sliding-window"],
        provenance=MachineProvenance(
            model="a-model",
            effort="medium",
            prompt_hash="0123456789ab",
            call_id="call-1",
            pin="a-host",
            temperature=0.0,
        ),
    )

    assert claim.source is ClaimSource.CLASSIFIER
    assert (claim.model, claim.prompt_hash, claim.call_id) == (
        "a-model",
        "0123456789ab",
        "call-1",
    )


def test_a_code_outside_the_vocabulary_is_rejected_whole():
    """This is a write path that could introduce an unrecognised code, and a
    claim asserts one set — so the half that passed is not written."""
    with pytest.raises(ValueError, match="unknown technique code"):
        machine_solution_claim(
            "s1",
            ["sliding-window", "invented"],
            provenance=MachineProvenance(
                model="a-model",
                effort="medium",
                prompt_hash="0123456789ab",
                call_id="call-1",
                pin="a-host",
            ),
        )
