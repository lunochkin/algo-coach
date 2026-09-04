from generating import CANONICAL, draft
from helpers import a_call

from algo_coach.generation import Writing
from algo_coach.generation.generator import read
from algo_coach.schema import ProblemDifficulty, WritingState

GENERATED = read(draft())


def test_the_draft_carries_the_id_its_site_outcomes_group_under():
    """One attempt, one id: a draft of its own would need a second reference
    to reach the four records of the same writing."""
    writing = Writing(template_id="t1")

    assert writing.draft(GENERATED, a_call()).id == writing.id


def test_the_draft_holds_what_the_generator_returned():
    """The five parts of one call, which is the whole of a draft before any
    step after it has run."""
    made = Writing().draft(GENERATED, a_call())

    assert made.state is WritingState.DRAFTED
    assert made.title == "Widest fair stretch"
    assert made.canonical == CANONICAL
    assert [case.expected for case in made.declared] == [3]
    assert made.difficulty is ProblemDifficulty.MEDIUM


def test_the_draft_copies_the_generator_call_whole():
    """A resume starts at the first step whose configuration or digest moved,
    and a copy taken partly could be compared with nothing."""
    made = Writing().draft(GENERATED, a_call())

    assert (made.generator.call_id, made.generator.model) == ("call-1", "a-model")
    assert made.blind is None


def test_the_draft_names_the_form_it_was_briefed_on():
    """A resume reads the template's `speedup`, and a sweep over the store has
    nothing else to find it from."""
    assert Writing(template_id="t1").draft(GENERATED, a_call()).template_id == "t1"


def test_an_unrecorded_attempt_names_no_form():
    """As its site outcomes name none: nothing recorded the attempt, so there
    is no template to read back."""
    assert Writing().draft(GENERATED, a_call()).template_id is None


def test_a_first_attempt_cites_no_draft():
    """Most drafts are written rather than re-run."""
    assert Writing().draft(GENERATED, a_call()).rerun_of is None


def test_a_re_run_cites_the_draft_it_came_from():
    """Re-running a rejected draft's failing step mints a new draft, and the
    one the gate stopped stays readable."""
    made = Writing().draft(GENERATED, a_call(), rerun_of="w0")

    assert made.rerun_of == "w0"


def test_two_attempts_are_two_drafts():
    """The id is minted per attempt, so nothing written for one reaches
    another."""
    assert Writing().draft(GENERATED, a_call()).id != Writing().draft(GENERATED, a_call()).id
