import pytest
from pydantic import ValidationError

from algo_coach.schema import Discard, Draft, ProblemStatus, SiteOutcome, WritingState

CONTENT = {"id": "w1"}


def make_draft(**overrides) -> Draft:
    return Draft.model_validate(CONTENT | overrides)


def test_the_states_are_the_steps_that_can_fail():
    """One per step of `flows.md`'s sequence, plus the terminal rejection. A
    step with no state of its own could not be resumed from."""
    assert [state.value for state in WritingState] == [
        "drafted",
        "checked",
        "referenced",
        "agreed",
        "built",
        "searched",
        "hardened",
        "landed",
        "rejected",
    ]


def test_the_two_machines_stay_apart():
    """`ProblemStatus` governs a problem that exists, this one the writing. One
    enum would put `drafted` beside `active` and every reader would branch."""
    assert not {state.value for state in WritingState} & {s.value for s in ProblemStatus}


def test_a_draft_starts_at_the_first_step():
    """The generator's answer is what a draft holds before anything checked
    it."""
    draft = make_draft()

    assert draft.state is WritingState.DRAFTED
    assert draft.gate is None


def test_a_draft_is_identified_by_the_writing_id():
    """`SiteOutcome` already mints one per attempt, so the four site records of
    one draft group with no new reference."""
    assert make_draft().id == "w1"
    assert "writing_id" in SiteOutcome.model_fields


def test_a_blank_id_is_rejected():
    """It passes a presence check while naming nothing, and the site outcomes
    would then group under it."""
    with pytest.raises(ValidationError, match="id"):
        make_draft(id="")


@pytest.mark.parametrize("gate", list(Discard))
def test_a_rejected_draft_names_the_gate_that_reached_it(gate):
    """Terminal means no resume rather than no record: what the gate said is
    the whole of what the attempt left."""
    draft = make_draft(state="rejected", gate=gate)

    assert draft.gate is gate


def test_the_gate_is_the_one_a_site_outcome_carries():
    """The same rejection read from two records. A second vocabulary would let
    a draft name a gate no site could file."""
    assert Draft.model_fields["gate"].annotation == SiteOutcome.model_fields["gate"].annotation


def test_a_rejected_draft_must_say_which_gate():
    """Whether the answer was wrong or merely unfinished is read off the gate,
    so a rejection without one could be resumed by whichever reader guessed."""
    with pytest.raises(ValidationError, match="gate"):
        make_draft(state="rejected")


@pytest.mark.parametrize("state", [s for s in WritingState if s is not WritingState.REJECTED])
def test_a_draft_still_being_written_carries_no_gate(state):
    """It would name a rejection that did not happen."""
    with pytest.raises(ValidationError, match="gate"):
        make_draft(state=state, gate="disagreed")


def test_an_unnamed_state_is_rejected():
    with pytest.raises(ValidationError, match="state"):
        make_draft(state="halfway")


def test_an_unnamed_gate_is_rejected():
    with pytest.raises(ValidationError, match="gate"):
        make_draft(state="rejected", gate="wrong")
