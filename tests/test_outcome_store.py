import pytest
from helpers import PROVENANCE
from pydantic import ValidationError

from algo_coach.calls import Configuration
from algo_coach.mint import site_outcome
from algo_coach.outcomes import OutcomeLog, answered
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


def test_a_record_answers_for_the_configuration_that_wrote_it():
    """A second configuration is paid for where it has not read, or a cheaper
    model would be scored on what the first one answered."""
    stored = [left(CallSite.BLIND, problem_id="p1")]
    asked = {"site": CallSite.BLIND, "problem_id": "p1", "prompt_hash": "0123456789ab"}
    mine = Configuration(model="a-model", effort="medium", pin=stored[0].pin)
    theirs = Configuration(model="another", effort="medium", pin=stored[0].pin)

    assert answered(stored, configuration=mine, **asked)
    assert not answered(stored, configuration=theirs, **asked)


def test_a_record_at_another_digest_does_not_answer():
    """The criteria travel with the prompt, so an edit re-asks what it reaches
    and leaves the rest."""
    stored = [left(CallSite.BLIND, problem_id="p1")]
    mine = Configuration(model="a-model", effort="medium", pin=stored[0].pin)

    assert not answered(
        stored, site=CallSite.BLIND, problem_id="p1", configuration=mine, prompt_hash="ffffffffffff"
    )


def test_a_record_on_another_problem_does_not_answer():
    """The item is the problem, and a site answers one at a time."""
    stored = [left(CallSite.BLIND, problem_id="p1")]
    mine = Configuration(model="a-model", effort="medium", pin=stored[0].pin)

    assert not answered(
        stored, site=CallSite.BLIND, problem_id="p2", configuration=mine, prompt_hash="0123456789ab"
    )
