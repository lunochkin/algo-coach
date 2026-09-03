import pytest

from algo_coach.schema import Card, CardSeed, Template, TemplateSeed

MINTED = frozenset({"id"})

# A card is authored once and seeded anywhere: only its id is per engine.
CONTRACTS = [(CardSeed, Card), (TemplateSeed, Template)]


@pytest.mark.parametrize(("seed", "record"), CONTRACTS)
def test_every_payload_field_lands_on_the_record(seed, record):
    """Nothing but this keeps the authored shape and the stored one aligned."""
    assert set(seed.model_fields) <= set(record.model_fields)


@pytest.mark.parametrize(("seed", "record"), CONTRACTS)
def test_payload_has_no_field_for_what_the_engine_mints(seed, record):
    """A field an author cannot name is a field they cannot forge."""
    assert not set(seed.model_fields) & MINTED


@pytest.mark.parametrize(("seed", "record"), CONTRACTS)
def test_payload_requires_what_the_record_requires(seed, record):
    """Seeding builds the record without catching a second validation error, so
    a field required there and optional here would crash the batch."""
    required = {name for name, field in record.model_fields.items() if field.is_required()}
    supplied = {name for name, field in seed.model_fields.items() if field.is_required()}
    assert required - MINTED <= supplied
