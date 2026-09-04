import pytest
from helpers import PROVENANCE, a_call
from pydantic import ValidationError

from algo_coach.schema import (
    Discard,
    Draft,
    ExpectedSource,
    MachineProvenance,
    ProblemDifficulty,
    ProblemStatus,
    SiteOutcome,
    WritingState,
)

# what the generator's call returned, which is the whole of a draft before any
# step after it has run
CONTENT = {
    "id": "w1",
    "title": "Two Sum",
    "statement": "Given an array, return ...",
    "canonical": "def solve(xs):\n    return len(xs)\n",
    "declared": [{"args": [[1, 2]], "expected": 2}],
    "difficulty": "easy",
}


def a_settled_case(**overrides) -> dict:
    return {
        "args": [[1, 2]],
        "expected": 2,
        "expected_from": "reference",
        "written": MachineProvenance.of(a_call()),
    } | overrides


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
        "paced",
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


def test_the_form_a_draft_was_briefed_on_is_optional():
    """A technique brief names no form, as on `SiteOutcome`. A blank one is
    rejected: it passes a presence check while naming nothing."""
    assert make_draft().template_id is None
    assert make_draft(template_id="t1").template_id == "t1"
    with pytest.raises(ValidationError, match="template_id"):
        make_draft(template_id="")


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


def test_a_draft_holds_what_the_generator_returned():
    """The five parts of one call. A draft exists only once they do, since a
    call that returned nothing left no step to resume from."""
    draft = make_draft()

    assert draft.title == "Two Sum"
    assert draft.statement.startswith("Given an array")
    assert draft.canonical.startswith("def solve")
    assert [case.expected for case in draft.declared] == [2]
    assert draft.difficulty is ProblemDifficulty.EASY


@pytest.mark.parametrize("field", ["title", "statement", "canonical", "difficulty"])
def test_the_generator_step_is_required_whole(field):
    """One call wrote all of it, so a draft missing a part of it describes a
    reply that never arrived."""
    with pytest.raises(ValidationError, match=field):
        Draft.model_validate({name: value for name, value in CONTENT.items() if name != field})


def test_a_draft_with_no_declared_case_is_rejected():
    """The set written with the statement is what every later step is judged
    against, and a resume cannot re-derive it."""
    with pytest.raises(ValidationError, match="declared"):
        make_draft(declared=[])


def test_the_declared_cases_carry_what_the_call_said_they_return():
    """`expected` is the generator's own declaration, which the check step
    reads as a gate rather than as a source."""
    assert make_draft().declared[0].expected == 2


def test_the_steps_after_the_generator_start_empty():
    """A draft is written at the first step and revised at each one after it,
    so absence is how far it got."""
    draft = make_draft()

    assert draft.reference is None
    assert draft.cases == []
    assert draft.builder is None and draft.largest is None
    assert draft.naive is None
    assert draft.separating is None
    assert draft.won == []


def test_a_draft_holds_the_reference_it_was_written_with():
    """A second call from the statement alone, which no local run
    re-derives."""
    assert make_draft(reference="def solve(xs): ...").reference == "def solve(xs): ..."


def test_a_draft_holds_the_cases_the_runs_settled():
    """Whose answer each case carries is what the two runs established, where
    `declared` holds what the generator asserted."""
    draft = make_draft(cases=[a_settled_case()])

    assert draft.cases[0].expected_from is ExpectedSource.REFERENCE
    assert draft.cases[0].written.call_id == "call-1"


def test_a_draft_holds_the_builder_and_its_bound():
    """One call returned both: the code that builds an input of a given size,
    and the largest size the statement admits."""
    draft = make_draft(builder="def solve(size, seed): ...", largest=1000)

    assert draft.builder.startswith("def solve")
    assert draft.largest == 1000


def test_a_draft_holds_the_clock_the_search_measures_against():
    """A resume holding neither the code nor its configuration would re-pay
    the call that wrote it."""
    draft = make_draft(naive="def solve(xs): ...", clock=PROVENANCE)

    assert draft.naive.startswith("def solve")
    assert draft.clock.call_id == "call-1"


@pytest.mark.parametrize("half", [{"builder": "def solve(size, seed): ..."}, {"largest": 1000}])
def test_half_a_builder_is_rejected(half):
    """A bound without code stops no search, and code without one lets a search
    ask for an input the problem excludes."""
    with pytest.raises(ValidationError, match="bound"):
        make_draft(**half)


def test_a_draft_holds_the_separating_case_apart_from_the_set():
    """It is appended after the loop, so a draft holding it in `cases` would
    put it in the set the survivors were decided against."""
    draft = make_draft(separating=a_settled_case(round=None))

    assert draft.separating.round is None
    assert draft.cases == []


def test_a_draft_holds_the_cases_the_rounds_won():
    """A proposal that killed nothing never lands, so this is what the rounds
    were paid for."""
    draft = make_draft(won=[a_settled_case(round=1)])

    assert [case.round for case in draft.won] == [1]


def test_a_draft_carries_the_configuration_of_each_step():
    """A resume starts at the first step whose configuration or digest moved,
    which is why both are held here rather than only the outputs."""
    for site in ("generator", "blind", "inputs", "clock", "discrimination"):
        draft = make_draft(**{site: PROVENANCE})

        assert getattr(draft, site).call_id == "call-1"


def test_a_step_runs_at_no_configuration_until_it_has_run():
    """Absence says the step was never asked, as it does on a site outcome."""
    assert make_draft().generator is None


@pytest.mark.parametrize("missing", PROVENANCE)
def test_a_step_copies_a_whole_configuration(missing):
    """All of it or none: a step whose configuration is partly unknown cannot
    be compared with the one a resume would run."""
    kept = {field: value for field, value in PROVENANCE.items() if field != missing}
    with pytest.raises(ValidationError, match=missing):
        make_draft(generator=kept)


def test_the_mutants_and_the_counters_are_not_held():
    """A tree walk enumerates the first and subprocesses kill them, so a resume
    re-derives both. The counters sit on the site outcomes of this id."""
    assert not {"mutants", "survived", "won_count", "rounds"} & set(Draft.model_fields)


def test_a_rejected_draft_cites_nothing_and_nothing_cites_it():
    """Terminal: its gate says the answer was wrong, and no draft is written
    from it. What it is kept for is the record of what the gate rejected."""
    assert "rerun_of" not in Draft.model_fields


def test_a_draft_that_has_not_landed_names_no_problem():
    """The id exists only once the problem is stored, so absence is every state
    before it."""
    assert make_draft().problem_id is None


def test_a_landed_draft_names_the_problem_it_became():
    """A crash between landing and clearing leaves this, and it is what tells
    the next run to clear rather than write the problem a second time."""
    assert make_draft(state="landed", problem_id="p1").problem_id == "p1"


def test_a_landed_draft_must_say_which_problem():
    """Without it the next run cannot tell a landed draft from one that stopped
    before landing, and would write the problem twice."""
    with pytest.raises(ValidationError, match="problem_id"):
        make_draft(state="landed")


@pytest.mark.parametrize("state", [WritingState.HARDENED, WritingState.REJECTED])
def test_a_draft_that_did_not_land_carries_no_problem(state):
    """It would name a landing that did not happen."""
    gate = {"gate": "disagreed"} if state is WritingState.REJECTED else {}
    with pytest.raises(ValidationError, match="problem_id"):
        make_draft(state=state, problem_id="p1", **gate)
