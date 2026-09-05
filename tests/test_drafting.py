import pytest
from generating import CANONICAL, FakeWriter, Raises
from matching import card, seeded, template

from algo_coach.calls import CallLog
from algo_coach.drafts import DraftStore
from algo_coach.generation import Corpus, reject, write_problems
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Discard, Draft, WritingState

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"
WRONG = "def solve(xs):\n    return len(xs) + 1\n"
# the search runs where a speedup is claimed, and holds the draft where nothing
# separated
CLAIMS = template("longest-valid-window", speedup=True)


def run(tmp_path, model: FakeWriter, **overrides):
    """One problem, with the store the run writes each step's draft to."""
    (one,) = seeded(tmp_path, card(**overrides))
    drafts = DraftStore(tmp_path)
    result = write_problems(
        model, CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path), drafts=drafts
    )
    return result, drafts


def written(tmp_path, model: FakeWriter, **overrides):
    """The draft a stopped run left behind."""
    _, drafts = run(tmp_path, model, **overrides)
    (stored,) = drafts.all()
    return stored


def test_a_landed_draft_is_cleared(tmp_path):
    """The problem it became is what a reader finds, and nothing in the draft
    is re-derivable from anywhere else."""
    result, drafts = run(tmp_path, FakeWriter())

    (landed,) = result.drafted
    assert landed.state is WritingState.LANDED
    assert landed.problem_id is not None
    assert drafts.all() == []


def test_a_draft_naming_a_problem_is_cleared_by_the_next_run(tmp_path):
    """A run that died between landing and clearing leaves one, and writing
    its problem a second time is the only other way to finish it."""
    (one,) = seeded(tmp_path, card())
    drafts = DraftStore(tmp_path)
    write_problems(
        FakeWriter(), CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path), drafts=drafts
    )
    corpus = Corpus.at(tmp_path)
    (problem,) = corpus.problems.all()
    drafts.put(a_landed_draft(problem.id))

    write_problems(FakeWriter(), CallLog(tmp_path), one, one.templates[0], corpus, drafts=drafts)

    assert drafts.all() == []
    assert len(corpus.problems.all()) == 2


def test_a_canonical_yielding_no_value_stops_at_the_first_gate(tmp_path):
    """Nothing establishes what the case returns, so the draft is rejected
    before a reference is written for it."""
    crashes = "def solve(xs):\n    raise ValueError(xs)\n"
    stored = written(tmp_path, FakeWriter(canonical=crashes))

    assert stored.state is WritingState.REJECTED
    assert stored.gate is Discard.NO_VALUE
    assert stored.reference is None


def test_a_canonical_contradicting_its_own_cases_is_settled_by_the_reference(tmp_path):
    """The declaration and the code came from one call, so what rejects the
    draft is the blind reading rather than the contradiction."""
    stored = written(tmp_path, FakeWriter(canonical=WRONG))

    assert stored.state is WritingState.REJECTED
    assert stored.gate is Discard.DISAGREED
    assert stored.blind is not None


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
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    result, _ = run(tmp_path, FakeWriter(slow=SLOW, generator=BUILDS), templates=[CLAIMS])
    (stored,) = result.drafted

    assert stored.canonical == CANONICAL
    assert [case.expected for case in stored.declared] == [3]
    assert [case.expected for case in stored.cases] == [3]
    assert (stored.builder, stored.largest) == (BUILDS, 8)
    assert stored.separating is not None


def test_each_step_copies_the_configuration_of_its_own_call(tmp_path):
    """A resume starts at the first step whose configuration or digest moved,
    so a draft holding one for the run would answer for every step."""
    result, _ = run(tmp_path, FakeWriter(generator=BUILDS))

    (stored,) = result.drafted
    assert stored.generator.call_id != stored.blind.call_id
    assert stored.inputs.call_id not in (stored.generator.call_id, stored.blind.call_id)


def test_the_draft_and_its_site_outcomes_carry_one_id(tmp_path):
    """The writing id, which is what groups the four records of one attempt
    with the draft they were written through."""
    (one,) = seeded(tmp_path, card())
    outcomes = OutcomeLog(tmp_path)
    result = write_problems(
        FakeWriter(),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=DraftStore(tmp_path),
        outcomes=outcomes,
    )

    (stored,) = result.drafted
    assert {left.writing_id for left in outcomes.outcomes()} == {stored.id}


def test_a_separated_problem_lands(tmp_path, monkeypatch):
    """The case that demonstrates the claim is stored, so the draft runs on
    through the loop."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    model = FakeWriter(slow=SLOW, generator=BUILDS)

    result, drafts = run(tmp_path, model, templates=[CLAIMS])

    (landed,) = result.drafted
    assert landed.state is WritingState.LANDED
    assert landed.separating is not None
    assert (result.held, drafts.all()) == ([], [])


def test_an_unseparated_draft_is_held_at_the_search(tmp_path):
    """The reference finished at every size the builder wrote, so nothing
    demonstrates the speedup its template claims and the problem does not
    land."""
    result, drafts = run(tmp_path, FakeWriter(generator=BUILDS), templates=[CLAIMS])

    (one,) = result.held
    stored = one.draft
    assert stored.state is WritingState.SEARCHED
    assert one.unseparated == "naive_finished"
    assert (stored.separating, stored.problem_id) == (None, None)
    # kept where it stopped, since a resume is what separates it
    assert drafts.all() == [stored]
    assert (result.drafted, ProblemStore(tmp_path).all()) == ([], [])


def a_landed_draft(problem_id: str) -> Draft:
    """What a run that died between landing and clearing leaves behind."""
    return Draft(
        id="w0",
        state=WritingState.LANDED,
        problem_id=problem_id,
        title="Widest fair stretch",
        statement="Given a list of readings, return ...",
        canonical=CANONICAL,
        declared=[{"args": [[1, 2, 3]], "expected": 3}],
        difficulty="medium",
    )


def test_a_draft_a_raised_call_left_is_held_with_its_reason(tmp_path):
    """The steps before it wrote to the store, so a run reporting only the
    failure would read as a problem nothing was paid for."""
    result, drafts = run(tmp_path, Raises())

    (one,) = result.held
    assert one.draft.state is WritingState.CHECKED
    assert "gateway" in one.failed
    assert [failed.index for failed in result.failed] == [1]
    assert drafts.all() == [one.draft]


def test_a_held_draft_is_rejected_where_the_reference_wrote_the_form(tmp_path):
    """The exit no resume reaches: that solution is immutable and it is still
    the clock, so the claim holds and this problem does not exercise it."""
    result, drafts = run(tmp_path, FakeWriter(generator=BUILDS), templates=[CLAIMS])
    (one,) = result.held
    stored = one.draft

    rejected = reject(drafts, stored)

    assert rejected.state is WritingState.REJECTED
    assert rejected.gate is Discard.UNEXERCISED
    assert drafts.get(stored.id).gate is Discard.UNEXERCISED


def test_a_landed_draft_is_not_rejected():
    """Its problem carries attempts, and what answers there is a retirement."""
    with pytest.raises(ValueError, match="landed"):
        reject(None, a_landed_draft("p1"))


def test_a_rejected_draft_is_not_rejected_a_second_time(tmp_path):
    """Terminal, and a second gate would overwrite what the first one said."""
    stored = written(tmp_path, FakeWriter(canonical=WRONG))

    with pytest.raises(ValueError, match="rejected"):
        reject(None, stored)


def test_a_run_without_a_store_writes_no_draft(tmp_path):
    """Silent by default, as `Writing` is: a test needs no store to call the
    run."""
    (one,) = seeded(tmp_path, card())
    write_problems(FakeWriter(), CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path))

    assert DraftStore(tmp_path).all() == []
