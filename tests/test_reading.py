"""A technique reading: which techniques one solution used.

The same question a claim answers about an attempt, and a different record —
the subject is code the engine wrote, and the answer is product data rather
than the user's own testimony.
"""

from datetime import UTC, datetime

import pytest
from helpers import PROVENANCE
from pydantic import ValidationError

from algo_coach.mint import machine_reading, user_reading
from algo_coach.schema import ReadingSource, TechniqueClaim, TechniqueReading


def make_reading(source: ReadingSource, **overrides) -> TechniqueReading:
    fields = {
        "id": "r1",
        "created_at": datetime.now(UTC),
        "solution_id": "s1",
        "techniques": ["sliding-window"],
        "source": source,
    } | overrides
    return TechniqueReading.model_validate(fields)


def test_a_reading_is_keyed_to_a_solution():
    """A technique is displayed by code, so the subject is the solution rather
    than the problem it answers."""
    assert make_reading(ReadingSource.USER).solution_id == "s1"
    assert "attempt_id" not in TechniqueReading.model_fields


def test_a_solution_naming_nothing_is_rejected():
    """It passes a presence check while pointing at no code."""
    with pytest.raises(ValidationError, match="solution_id"):
        make_reading(ReadingSource.USER, solution_id="")


def test_one_record_names_every_technique_of_one_solution():
    """Asserted together, so a later reading replaces the whole set rather
    than merging with it."""
    reading = make_reading(ReadingSource.USER, techniques=["sliding-window", "two-pointers"])

    assert reading.techniques == ["sliding-window", "two-pointers"]


def test_an_empty_reading_is_a_verdict_rather_than_an_absence():
    """A reading is only ever written deliberately, so naming nothing says the
    vocabulary does not cover this code."""
    assert make_reading(ReadingSource.CLASSIFIER, techniques=[], **PROVENANCE).techniques == []


def test_a_reading_needs_no_decline():
    """A claim needs one because the drill loop records nothing where the user
    skips, which makes an empty claim ambiguous. Nothing skips here."""
    assert "declined" in TechniqueClaim.model_fields
    assert "declined" not in TechniqueReading.model_fields


def test_a_machine_reading_carries_its_whole_configuration():
    """One whose configuration is partly known compares with nothing."""
    with pytest.raises(ValidationError, match="machine reading needs"):
        make_reading(ReadingSource.CLASSIFIER)

    assert make_reading(ReadingSource.CLASSIFIER, **PROVENANCE).model == "a-model"


def test_a_hand_reading_carries_none_of_it():
    """Nothing re-derives it, so any of it would name a configuration that
    never touched the record."""
    with pytest.raises(ValidationError, match="hand reading carries no"):
        make_reading(ReadingSource.USER, **PROVENANCE)


def test_a_reading_records_what_its_author_saw():
    """Named one by one, so a record made after seeing one configuration is
    still independent of another."""
    assert make_reading(ReadingSource.USER).informed_by == []
    assert make_reading(ReadingSource.USER, informed_by=["call-1"]).informed_by == ["call-1"]


def test_the_two_writers_are_named_apart():
    """The user's stands over any machine reading however late, as a claim
    resolves."""
    assert set(ReadingSource) == {ReadingSource.USER, ReadingSource.CLASSIFIER}


def test_a_hand_reading_is_minted_blind_and_unconfigured():
    reading = user_reading("s1", ["sliding-window"])

    assert (reading.source, reading.solution_id) == (ReadingSource.USER, "s1")
    assert [field for field in reading.RECORDED if getattr(reading, field) is not None] == []
    assert reading.informed_by == []


def test_a_machine_reading_names_what_produced_it():
    """The digest is what makes it stale, so editing one criterion re-reads
    the solutions that criterion reached."""
    reading = machine_reading(
        "s1",
        ["sliding-window"],
        model="a-model",
        effort="medium",
        prompt_hash="0123456789ab",
        call_id="call-1",
        pin="a-host",
        temperature=0.0,
    )

    assert reading.source is ReadingSource.CLASSIFIER
    assert (reading.model, reading.prompt_hash, reading.call_id) == (
        "a-model",
        "0123456789ab",
        "call-1",
    )


def test_a_code_outside_the_vocabulary_is_rejected_whole():
    """This is a write path that could introduce an unrecognised code, and a
    reading asserts one set — so the half that passed is not written."""
    with pytest.raises(ValueError, match="unknown technique code"):
        machine_reading(
            "s1",
            ["sliding-window", "invented"],
            model="a-model",
            effort="medium",
            prompt_hash="0123456789ab",
            call_id="call-1",
            pin="a-host",
        )
