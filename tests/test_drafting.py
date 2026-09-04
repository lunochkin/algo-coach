from generating import CANONICAL, FakeWriter
from matching import card, seeded

from algo_coach.calls import CallLog
from algo_coach.drafts import DraftStore
from algo_coach.generation import Corpus, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.schema import Discard, WritingState

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"
WRONG = "def solve(xs):\n    return len(xs) + 1\n"


def written(tmp_path, model: FakeWriter, **overrides):
    """One problem, with the draft store the run writes each step to."""
    (one,) = seeded(tmp_path, card(**overrides))
    drafts = DraftStore(tmp_path)
    write_problems(
        model,
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=drafts,
    )
    (stored,) = drafts.all()
    return stored


def test_a_run_that_reached_the_end_leaves_the_draft_hardened(tmp_path):
    """The last step that can fail. Landing is what moves it further, and
    nothing clears it yet."""
    stored = written(tmp_path, FakeWriter())

    assert stored.state is WritingState.HARDENED
    assert stored.gate is None


def test_a_canonical_yielding_no_value_stops_at_the_first_gate(tmp_path):
    """Nothing establishes what the case returns, so the draft is rejected
    before a reference is written for it."""
    crashes = "def solve(xs):\n    raise ValueError(xs)\n"
    stored = written(tmp_path, FakeWriter(canonical=crashes))

    assert stored.state is WritingState.REJECTED
    assert stored.gate is Discard.NO_VALUE
    assert stored.reference is None


def test_a_canonical_contradicting_its_own_cases_pays_for_no_blind_call(tmp_path):
    """The call wrote one of the two wrong, and the statement it wrote is not
    worth a second reading."""
    stored = written(tmp_path, FakeWriter(canonical=WRONG))

    assert stored.state is WritingState.REJECTED
    assert stored.gate is Discard.MISDECLARED
    assert (stored.reference, stored.blind) == (None, None)


def test_the_reference_a_rejected_draft_paid_for_is_kept(tmp_path):
    """The blind call answered and the settling rejected it, so what the run
    bought stays readable."""
    stored = written(tmp_path, FakeWriter(solution=WRONG))

    assert stored.state is WritingState.REJECTED
    assert stored.gate is Discard.DISAGREED
    assert stored.reference == WRONG
    assert stored.blind is not None


def test_a_draft_holds_what_each_step_answered(tmp_path, monkeypatch):
    """The statement's own cases, the reference, the builder and its bound,
    each written as the step that produced it answered."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    stored = written(tmp_path, FakeWriter(solution=SLOW, generator=BUILDS))

    assert stored.canonical == CANONICAL
    assert [case.expected for case in stored.declared] == [3]
    assert [case.expected for case in stored.cases] == [3]
    assert (stored.builder, stored.largest) == (BUILDS, 8)
    assert stored.separating is not None


def test_each_step_copies_the_configuration_of_its_own_call(tmp_path):
    """A resume starts at the first step whose configuration or digest moved,
    so a draft holding one for the run would answer for every step."""
    stored = written(tmp_path, FakeWriter(generator=BUILDS))

    assert stored.generator.call_id != stored.blind.call_id
    assert stored.inputs.call_id not in (stored.generator.call_id, stored.blind.call_id)


def test_the_draft_and_its_site_outcomes_carry_one_id(tmp_path):
    """The writing id, which is what groups the four records of one attempt
    with the draft they were written through."""
    (one,) = seeded(tmp_path, card())
    drafts, outcomes = DraftStore(tmp_path), OutcomeLog(tmp_path)
    write_problems(
        FakeWriter(),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=drafts,
        outcomes=outcomes,
    )

    (stored,) = drafts.all()
    assert {left.writing_id for left in outcomes.outcomes()} == {stored.id}


def test_a_run_without_a_store_writes_no_draft(tmp_path):
    """Silent by default, as `Writing` is: a test needs no store to call the
    run."""
    (one,) = seeded(tmp_path, card())
    write_problems(FakeWriter(), CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path))

    assert DraftStore(tmp_path).all() == []
