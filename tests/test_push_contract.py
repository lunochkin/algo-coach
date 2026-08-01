"""The push models are the contract clients copy, and ingest builds a record
straight from one. Nothing but these tests keeps the two shapes aligned."""

import pytest

from algo_coach.schema import Attempt, AttemptPush, Problem, ProblemPush

# What ingest stamps, and so must never reach the payload.
ATTEMPT_STAMPED = frozenset({"id", "user_id", "problem_id", "origin"})
PROBLEM_STAMPED = frozenset({"id", "user_id", "owner", "techniques"})

CONTRACTS = [
    # `problem_external_id` is consumed by ingest to resolve the reference and
    # is the one payload field with no field on the record.
    (AttemptPush, Attempt, ATTEMPT_STAMPED, frozenset({"problem_external_id"})),
    (ProblemPush, Problem, PROBLEM_STAMPED, frozenset()),
]


@pytest.mark.parametrize(("push", "record", "stamped", "consumed"), CONTRACTS)
def test_every_payload_field_lands_on_the_record(push, record, stamped, consumed):
    assert set(push.model_fields) - consumed <= set(record.model_fields)


@pytest.mark.parametrize(("push", "record", "stamped", "consumed"), CONTRACTS)
def test_payload_has_no_field_for_what_the_engine_stamps(push, record, stamped, consumed):
    """A field a client cannot name is a field it cannot forge."""
    assert not set(push.model_fields) & stamped


@pytest.mark.parametrize(("push", "record", "stamped", "consumed"), CONTRACTS)
def test_payload_requires_what_the_record_requires(push, record, stamped, consumed):
    """Ingest builds the record without catching a second validation error, so
    a field required there and optional here would crash the batch."""
    required = {name for name, field in record.model_fields.items() if field.is_required()}
    supplied = {name for name, field in push.model_fields.items() if field.is_required()}
    assert required - stamped <= supplied
