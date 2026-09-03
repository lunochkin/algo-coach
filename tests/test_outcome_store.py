"""What each call site left, appended.

A second run of one site over one item is a second record, as a second
verification is: neither answers for the other.
"""

import pytest
from helpers import PROVENANCE
from pydantic import ValidationError

from algo_coach.mint import site_outcome
from algo_coach.outcomes import OutcomeLog
from algo_coach.schema import CallSite, Discard, SiteOutcome


def left(site: CallSite = CallSite.GENERATOR, writing_id: str = "w1", **overrides):
    return site_outcome(site, writing_id, "t1", **(PROVENANCE | overrides))


def test_an_empty_store_reads_as_nothing(tmp_path):
    assert OutcomeLog(tmp_path).outcomes() == []
    assert OutcomeLog(tmp_path).for_writing("w1") == []


def test_a_record_reads_back_whole(tmp_path):
    """The gate and the counters are what an eval reads, so they survive the
    round trip rather than collapsing to whether the problem landed."""
    store = OutcomeLog(tmp_path)
    one = left(CallSite.DISCRIMINATION, gate=Discard.DISAGREED, mutants=53, survived=5, won=15)
    store.append(one)

    read = store.outcomes()

    assert read == [one]
    assert read[0].gate is Discard.DISAGREED


def test_records_are_read_per_attempt(tmp_path):
    """The writing id is what groups a draft's sites, landed or not."""
    store = OutcomeLog(tmp_path)
    mine = [left(CallSite.GENERATOR, "w1"), left(CallSite.BLIND, "w1")]
    theirs = left(CallSite.GENERATOR, "w2")
    for one in [*mine, theirs]:
        store.append(one)

    assert store.for_writing("w1") == mine
    assert store.for_writing("w2") == [theirs]


def test_a_record_carries_its_whole_configuration(tmp_path):
    """A site whose configuration is partly unknown compares with nothing."""
    with pytest.raises(ValidationError, match="needs pin"):
        SiteOutcome(
            id="o1",
            created_at="2026-01-01T00:00:00Z",
            site=CallSite.BLIND,
            writing_id="w1",
            template_id="t1",
            model="a-model",
            effort="medium",
            prompt_hash="0123456789ab",
            call_id="call-1",
        )
