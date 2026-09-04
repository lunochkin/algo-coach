import pytest
from generating import CANONICAL, FakeWriter, Raises
from matching import card, seeded, template

from algo_coach.calls import CallLog, Configuration
from algo_coach.drafts import DraftStore
from algo_coach.generation import (
    BENCH,
    ORDER,
    Bench,
    Corpus,
    Notes,
    blind,
    clock,
    inputs,
    moved_at,
    resume,
    write_problems,
)
from algo_coach.outcomes import OutcomeLog
from algo_coach.schema import CallSite, Draft, Template, WritingState

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
# four mutation sites, so a survivor reaches a round and the loop pays a call
BRANCHING = "def solve(n):\n    return n > 3\n"
AGREES = "def solve(n):\n    return not n <= 3\n"
DECIDES = [{"args": "[0]", "expected": "false"}]
OTHER = Configuration(model="another-model", effort="medium", pin="a-provider/bf16")


# the form these drafts were written under, and the same one claiming the
# speedup that makes the search run
OPTIMUM = Template(id="t1", **template("longest-valid-window"))
CLAIMS = Template(id="t1", **template("longest-valid-window", speedup=True))


def drafted(tmp_path) -> Draft:
    """A draft every answering site left a configuration on."""
    (one,) = seeded(tmp_path, card())
    model = FakeWriter(
        canonical=BRANCHING,
        solution=AGREES,
        cases=DECIDES,
        generator=BUILDS,
        separators=[[[4], [3]]],
    )
    result = write_problems(
        model,
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=DraftStore(tmp_path),
    )
    (stored,) = result.drafted
    return stored


def test_every_state_but_the_terminal_one_is_in_the_order():
    """`reaches` indexes into it, so a state added to the enum and not here
    would raise on the draft that reached it."""
    assert list(ORDER) == [state for state in WritingState if state is not WritingState.REJECTED]


def test_an_unchanged_bench_moves_nothing(tmp_path):
    """The run wrote this draft at the bench's own configurations, and every
    digest is a function of the statement it already holds."""
    assert moved_at(drafted(tmp_path), OPTIMUM, BENCH) is None


def test_a_moved_blind_configuration_starts_at_the_reference(tmp_path):
    """The reference is written from the statement alone, so a second model
    reading it is a second reading rather than the stored one."""
    assert moved_at(drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"blind": OTHER})) is (
        WritingState.REFERENCED
    )


def test_a_moved_inputs_configuration_starts_at_the_builder(tmp_path):
    assert moved_at(drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"inputs": OTHER})) is (
        WritingState.BUILT
    )


def test_a_moved_discrimination_configuration_starts_at_the_loop(tmp_path):
    """Its digest carries the survivors, which only the local kill pass names,
    so the configuration is what answers here."""
    assert moved_at(
        drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"discrimination": OTHER})
    ) is (WritingState.HARDENED)


def test_the_earliest_moved_step_is_the_one_returned(tmp_path):
    """Where a resume starts, which is what the local steps after it run
    from."""
    bench = BENCH.model_copy(update={"blind": OTHER, "discrimination": OTHER})

    assert moved_at(drafted(tmp_path), OPTIMUM, bench) is WritingState.REFERENCED


def test_a_moved_generator_invalidates_no_draft(tmp_path):
    """The draft is that step's output, and a new prompt writes a different
    problem rather than the same one again."""
    assert (
        moved_at(drafted(tmp_path), OPTIMUM, BENCH.model_copy(update={"generator": OTHER})) is None
    )


def test_a_stale_digest_starts_at_its_own_step(tmp_path):
    """An edited prompt moves the digest without moving the configuration, and
    a resume that read only the model would re-run nothing."""
    stored = drafted(tmp_path)
    stale = stored.blind.model_copy(update={"prompt_hash": "ffffffffffff"})

    assert moved_at(stored.model_copy(update={"blind": stale}), OPTIMUM, BENCH) is (
        WritingState.REFERENCED
    )


def test_a_step_the_draft_never_took_is_not_moved():
    """What to do about a step that never ran is the draft's state, not the
    bench's."""
    stopped = Draft(
        id="w1",
        state=WritingState.CHECKED,
        title="Widest fair stretch",
        statement="Given a list of readings, return ...",
        canonical=CANONICAL,
        declared=[{"args": [[1, 2, 3]], "expected": 3}],
        difficulty="medium",
    )

    assert (
        moved_at(stopped, OPTIMUM, Bench(blind=OTHER, inputs=OTHER, discrimination=OTHER)) is None
    )


def held(tmp_path) -> Draft:
    """A draft the search held: its template claims a speedup and the reference
    finished at every size the builder wrote."""
    (one,) = seeded(tmp_path, card(templates=[template("longest-valid-window", speedup=True)]))
    result = write_problems(
        FakeWriter(generator=BUILDS),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=DraftStore(tmp_path),
    )
    (one,) = result.held
    return one.draft


def test_a_claim_that_still_stands_leaves_the_draft_at_the_search(tmp_path):
    """Nothing separated the two solutions, and the claim is what says a case
    has to."""
    assert moved_at(held(tmp_path), CLAIMS, BENCH) is None


def test_a_corrected_speedup_resumes_the_draft_the_search_held(tmp_path):
    """A flag edit moves neither a configuration nor a digest, so a resume
    reading only those would leave the draft where the search stopped it."""
    assert moved_at(held(tmp_path), OPTIMUM, BENCH) is WritingState.HARDENED


def test_a_moved_clock_configuration_starts_at_the_naive_solution(tmp_path):
    """A draft holds one only where a speedup is claimed, which is where the
    search that reads it runs."""
    bench = BENCH.model_copy(update={"clock": OTHER})

    assert moved_at(held(tmp_path), CLAIMS, bench) is WritingState.PACED


def test_an_edited_trigger_re_asks_the_clock_alone(tmp_path):
    """The one prompt carrying more than the statement, so editing a form
    re-asks the drafts written for it and leaves the rest."""
    edited = Template(id="t1", **template("longest-valid-window", speedup=True, trigger="Else."))

    assert moved_at(held(tmp_path), CLAIMS, BENCH) is None
    assert moved_at(held(tmp_path), edited, BENCH) is WritingState.PACED


def test_a_moved_configuration_is_returned_over_a_corrected_flag(tmp_path):
    """The reference is written before the search, and the earliest moved step
    is where the resume starts."""
    bench = BENCH.model_copy(update={"blind": OTHER})

    assert moved_at(held(tmp_path), OPTIMUM, bench) is WritingState.REFERENCED


SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"
CLAIMED = [template("longest-valid-window", speedup=True)]
WRONG = "def solve(xs):\n    return len(xs) + 1\n"


def written(tmp_path, model: FakeWriter, drafts: DraftStore, **overrides):
    """One card, and what a run that stopped left in the store."""
    (one,) = seeded(tmp_path, card(**overrides))
    result = write_problems(
        model,
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=drafts,
        outcomes=OutcomeLog(tmp_path),
    )
    return one, result


def test_a_moved_clock_re_pays_that_call_and_no_other(tmp_path, monkeypatch):
    """The reference and the input generator are written from the statement,
    which this bench did not move."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    drafts = DraftStore(tmp_path)
    one, first = written(tmp_path, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held
    model = FakeWriter(generator=BUILDS, slow=SLOW)

    result = resume(
        model,
        CallLog(tmp_path),
        one.templates[0],
        stopped.draft,
        Corpus.at(tmp_path),
        bench=BENCH.model_copy(update={"clock": OTHER}),
        drafts=drafts,
    )

    asked = [call["system"] for call in model.calls]
    assert clock.SYSTEM in asked
    assert blind.SYSTEM not in asked and inputs.SYSTEM not in asked
    assert result.started_at is WritingState.PACED
    # the new clock separated where the stored one did not, so the draft lands
    assert len(result.drafted) == 1


def test_a_resume_pays_for_the_step_that_had_no_answer_and_no_other(tmp_path, monkeypatch):
    """The draft holds the reference the first run bought, so the resume is
    charged for the input generator alone."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    drafts = DraftStore(tmp_path)
    one, first = written(tmp_path, FakeWriter(slow=SLOW), drafts, templates=CLAIMED)
    (stopped,) = first.held
    stages: list[str] = []
    model = FakeWriter(slow=SLOW, generator=BUILDS)

    result = resume(
        model,
        CallLog(tmp_path),
        one.templates[0],
        stopped.draft,
        Corpus.at(tmp_path),
        notes=Notes(lambda step: stages.append(f"{step.name}: {step.detail}")),
        drafts=drafts,
    )

    assert result.started_at is WritingState.BUILT
    assert "resume: starting at built" in stages
    assert blind.SYSTEM not in [asked["system"] for asked in model.calls]
    assert len(result.drafted) == 1
    # cleared, since the problem it became is what a reader finds
    assert drafts.all() == []


def test_a_draft_a_raised_call_left_resumes_at_that_call(tmp_path):
    """The steps before it stand, and the one that answered nothing is where
    the resume starts."""
    drafts = DraftStore(tmp_path)
    one, first = written(tmp_path, Raises(), drafts)
    (stopped,) = first.held
    assert stopped.draft.state is WritingState.CHECKED

    result = resume(
        FakeWriter(),
        CallLog(tmp_path),
        one.templates[0],
        stopped.draft,
        Corpus.at(tmp_path),
        drafts=drafts,
    )

    assert result.started_at is WritingState.REFERENCED
    assert len(result.drafted) == 1


def test_a_resumed_step_writes_a_second_site_outcome(tmp_path):
    """Never an amendment, as a re-run of any site over one item does. Both
    group under the writing id the draft carries."""
    drafts = DraftStore(tmp_path)
    one, first = written(tmp_path, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held

    resume(
        FakeWriter(generator=BUILDS),
        CallLog(tmp_path),
        one.templates[0],
        stopped.draft,
        Corpus.at(tmp_path),
        bench=BENCH.model_copy(update={"blind": OTHER}),
        outcomes=OutcomeLog(tmp_path),
        drafts=drafts,
    )

    read = [left for left in OutcomeLog(tmp_path).outcomes() if left.site is CallSite.BLIND]
    assert [left.model for left in read] == [BENCH.blind.model, OTHER.model]
    assert {left.writing_id for left in read} == {stopped.draft.id}


def test_a_resume_that_holds_again_leaves_the_draft_where_it_stopped(tmp_path):
    """Forward only: the local steps run again, and a draft moved back would
    re-pay the calls it holds if the run then died."""
    drafts = DraftStore(tmp_path)
    one, first = written(tmp_path, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held

    result = resume(
        FakeWriter(generator=BUILDS),
        CallLog(tmp_path),
        one.templates[0],
        stopped.draft,
        Corpus.at(tmp_path),
        drafts=drafts,
    )

    (again,) = result.held
    assert again.draft.state is WritingState.SEARCHED
    assert drafts.get(stopped.draft.id).state is WritingState.SEARCHED


def test_a_moved_blind_configuration_re_pays_no_input_generator(tmp_path):
    """Both prompts are the statement alone, so neither site invalidates the
    other."""
    drafts = DraftStore(tmp_path)
    one, first = written(tmp_path, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held
    model = FakeWriter(generator=BUILDS)

    result = resume(
        model,
        CallLog(tmp_path),
        one.templates[0],
        stopped.draft,
        Corpus.at(tmp_path),
        bench=BENCH.model_copy(update={"blind": OTHER}),
        drafts=drafts,
    )

    asked = [call["system"] for call in model.calls]
    assert blind.SYSTEM in asked
    assert inputs.SYSTEM not in asked
    (again,) = result.held
    assert again.draft.inputs == stopped.draft.inputs


def test_a_rejected_draft_is_not_resumed(tmp_path):
    """Its gate said the answer was wrong, so a resume skipping that gate would
    land what the gate rejected."""
    drafts = DraftStore(tmp_path)
    one, _ = written(tmp_path, FakeWriter(canonical=WRONG), drafts)
    (gated,) = drafts.all()

    with pytest.raises(ValueError, match="rejected"):
        resume(FakeWriter(), CallLog(tmp_path), one.templates[0], gated, Corpus.at(tmp_path))
