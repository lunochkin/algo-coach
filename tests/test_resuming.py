import pytest
from generating import CANONICAL, FakeWriter, Raises
from matching import card, seeded, template

from algo_coach.calls import CallLog
from algo_coach.drafts import DraftStore
from algo_coach.generation import (
    BENCH,
    ORDER,
    Bench,
    Corpus,
    Notes,
    Progress,
    Target,
    advances,
    blind,
    inputs,
    moved_at,
    naive,
    resume,
    sending,
    write_problems,
)
from algo_coach.generation.speedup import CEILING, MARGIN, REPEATS_MAX, SEARCH_REVISION
from algo_coach.outcomes import OutcomeLog
from algo_coach.schema import CallSite, Card, Configuration, Draft, WritingState

BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
# four mutation sites, so a survivor reaches a round and the loop pays a call
BRANCHING = "def solve(n):\n    return n > 3\n"
AGREES = "def solve(n):\n    return not n <= 3\n"
DECIDES = [{"args": "[0]", "expected": "false"}]
OTHER = Configuration(model="another-model", effort="medium", pin="a-provider/bf16")


def aimed(one: dict) -> Target:
    """A card and one of its templates, as a run aims at them. The naive
    site's prompt is built from both."""
    stored = Card.model_validate(card() | {"id": "c1", "templates": [{"id": "t1", **one}]})
    return Target(card=stored, template=stored.templates[0])


# the form these drafts were written under, and the same one claiming the
# speedup that makes the search run
OPTIMUM = aimed(template("longest-valid-window"))
CLAIMS = aimed(template("longest-valid-window", speedup=True))


def drafted(database) -> Draft:
    """A draft every answering site left a configuration on."""
    (one,) = seeded(database, card())
    model = FakeWriter(
        canonical=BRANCHING,
        solution=AGREES,
        cases=DECIDES,
        generator=BUILDS,
        separators=[[[4], [3]]],
    )
    result = write_problems(
        model,
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
        drafts=DraftStore(database),
    )
    (stored,) = result.drafted
    return stored


def test_every_state_but_the_terminal_one_is_in_the_order():
    """`reaches` indexes into it, so a state added to the enum and not here
    would raise on the draft that reached it."""
    assert list(ORDER) == [state for state in WritingState if state is not WritingState.REJECTED]


def test_an_unchanged_bench_moves_nothing(database):
    """The run wrote this draft at the bench's own configurations, and every
    prompt hash is a function of the statement it already holds."""
    assert moved_at(drafted(database), OPTIMUM, BENCH) is None


def test_a_moved_blind_configuration_starts_at_the_reference(database):
    """The reference is written from the statement alone, so a second model
    reading it is a second reading rather than the stored one."""
    assert moved_at(drafted(database), OPTIMUM, BENCH.model_copy(update={"blind": OTHER})) is (
        WritingState.REFERENCED
    )


def test_a_moved_inputs_configuration_starts_at_the_input_generator(database):
    assert moved_at(drafted(database), OPTIMUM, BENCH.model_copy(update={"inputs": OTHER})) is (
        WritingState.BUILT
    )


def test_a_moved_discrimination_configuration_starts_at_the_loop(database):
    """Its prompt hash carries the survivors, which only the local kill pass
    names, so the configuration is what answers here."""
    assert moved_at(
        drafted(database), OPTIMUM, BENCH.model_copy(update={"discrimination": OTHER})
    ) is (WritingState.HARDENED)


def test_the_earliest_moved_step_is_the_one_returned(database):
    """Where a resume starts, which is what the local steps after it run
    from."""
    bench = BENCH.model_copy(update={"blind": OTHER, "discrimination": OTHER})

    assert moved_at(drafted(database), OPTIMUM, bench) is WritingState.REFERENCED


def test_a_moved_generator_invalidates_no_draft(database):
    """The draft is that step's output, and a new prompt writes a different
    problem rather than the same one again."""
    assert (
        moved_at(drafted(database), OPTIMUM, BENCH.model_copy(update={"generator": OTHER})) is None
    )


def test_a_stale_prompt_hash_starts_at_its_own_step(database):
    """An edited prompt moves the prompt hash without moving the configuration,
    and a resume that read only the model would re-run nothing."""
    stored = drafted(database)
    stale = stored.blind_provenance.model_copy(update={"prompt_hash": "ffffffffffff"})

    assert moved_at(stored.model_copy(update={"blind_provenance": stale}), OPTIMUM, BENCH) is (
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


def held(database) -> Draft:
    """A draft the search held: its template claims a speedup and the reference
    finished at every size the input generator wrote."""
    (one,) = seeded(database, card(templates=[template("longest-valid-window", speedup=True)]))
    result = write_problems(
        FakeWriter(generator=BUILDS),
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
        drafts=DraftStore(database),
    )
    (one,) = result.held
    return one.draft


def test_an_unseparated_draft_draws_the_naive_solution_again(database):
    """Nothing about the bench moved, and the site is the one that is sampled:
    a second call is a second draw rather than the answer already stored."""
    stopped = held(database)

    assert stopped.unseparated == "naive_finished"
    assert moved_at(stopped, CLAIMS, BENCH) is WritingState.PACED


CRASHES = "def solve(size, seed):\n    raise ValueError\n"


def unbuilt(database) -> Draft:
    """A draft the search never ran for: the input generator's code crashed, so
    nothing timed the solution it holds."""
    (one,) = seeded(database, card(templates=[template("longest-valid-window", speedup=True)]))
    result = write_problems(
        FakeWriter(generator=CRASHES),
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
        drafts=DraftStore(database),
    )
    (stopped,) = result.held
    return stopped.draft


def test_a_search_that_never_ran_draws_no_naive_solution(database):
    """A draw would pay for a call the search still cannot use."""
    stopped = unbuilt(database)

    assert "built nothing at size 1" in stopped.unseparated
    assert moved_at(stopped, CLAIMS, BENCH) is None


def test_a_draft_a_resume_starts_past_the_search_on_advances_nowhere(database):
    """Nothing about the bench moved, so a resume starts at the loop, and a
    draft with no separating case is held before it."""
    assert not advances(unbuilt(database), CLAIMS, BENCH)


def test_a_draft_whose_naive_solution_is_drawn_again_advances(database):
    """The resume starts at the naive site, so the search runs again against
    the second draw."""
    assert advances(held(database), CLAIMS, BENCH)


def test_a_form_that_is_its_own_optimum_advances(database):
    """No search runs where no speedup is claimed, so nothing waits on the case
    one would have stored."""
    assert advances(held(database), OPTIMUM, BENCH)


def test_a_corrected_speedup_resumes_the_draft_the_search_held(database):
    """A flag edit moves neither a configuration nor a prompt hash, so a resume
    reading only those would leave the draft where the search stopped it."""
    assert moved_at(held(database), OPTIMUM, BENCH) is WritingState.HARDENED


def test_the_search_records_the_ceiling_it_ran_under(database):
    """A raised ceiling is what releases a draft the walk stopped at, and the
    draft is the only record of which ceiling that was."""
    assert held(database).ceiling == CEILING


def at_ceiling(database, reason: str, ceiling: int | None, **bounds) -> Draft:
    """A draft the search held at one of its bounds, as the search left it."""
    return held(database).model_copy(
        update={
            "unseparated": reason,
            "ceiling": ceiling,
            "margin": bounds.pop("margin", MARGIN),
            "repeats_max": bounds.pop("repeats_max", REPEATS_MAX),
            "search_revision": bounds.pop("search_revision", SEARCH_REVISION),
        }
    )


def test_a_moved_ceiling_re_enters_the_search(database):
    """A raised constant moves neither a configuration nor a prompt hash, and
    the walk it stopped is a local step that costs no call."""
    stopped = at_ceiling(database, "input_too_large", CEILING // 4)

    assert moved_at(stopped, CLAIMS, BENCH) is WritingState.SEARCHED
    assert advances(stopped, CLAIMS, BENCH)


def test_a_case_the_ceiling_would_not_hold_re_enters_the_search_too(database):
    """The speedup was proved and the case lost, so a larger ceiling is exactly
    what the draft waits on."""
    assert moved_at(at_ceiling(database, "case_too_large", CEILING // 4), CLAIMS, BENCH) is (
        WritingState.SEARCHED
    )


def test_a_draft_searched_under_the_current_ceiling_waits(database):
    """Nothing moved, so a resume would walk the same sizes to the same stop."""
    stopped = at_ceiling(database, "input_too_large", CEILING)

    assert moved_at(stopped, CLAIMS, BENCH) is None
    assert not advances(stopped, CLAIMS, BENCH)


def test_a_draft_searched_before_the_ceiling_was_recorded_re_enters_the_search(database):
    """Absent is not the current ceiling: the drafts written before the field
    existed were walked under the 64 KiB one."""
    assert moved_at(at_ceiling(database, "input_too_large", None), CLAIMS, BENCH) is (
        WritingState.SEARCHED
    )


def test_a_naive_solution_that_finished_draws_again_whatever_the_ceiling(database):
    """The walk reached the bound, not the ceiling, so a larger ceiling changes
    nothing it would build."""
    assert moved_at(at_ceiling(database, "naive_finished", None), CLAIMS, BENCH) is (
        WritingState.PACED
    )


def test_a_moved_naive_solution_configuration_starts_at_the_naive_solution(database):
    """A draft holds one only where a speedup is claimed, which is where the
    search that reads it runs."""
    bench = BENCH.model_copy(update={"naive": OTHER})

    assert moved_at(held(database), CLAIMS, bench) is WritingState.PACED


def test_an_edited_trigger_re_asks_the_naive_solution_alone(database):
    """The one prompt carrying more than the statement, so editing a form
    moves the prompt hash of the drafts written for it and no others."""
    edited = aimed(template("longest-valid-window", speedup=True, trigger="Else."))

    written_at = held(database).naive_provenance.prompt_hash

    assert moved_at(held(database), edited, BENCH) is WritingState.PACED
    assert sending(held(database), "naive", edited) != written_at


def test_a_moved_configuration_is_returned_over_a_corrected_flag(database):
    """The reference is written before the search, and the earliest moved step
    is where the resume starts."""
    bench = BENCH.model_copy(update={"blind": OTHER})

    assert moved_at(held(database), OPTIMUM, bench) is WritingState.REFERENCED


SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"
CLAIMED = [template("longest-valid-window", speedup=True)]
WRONG = "def solve(xs):\n    return len(xs) + 1\n"


def written(database, model: FakeWriter, drafts: DraftStore, **overrides):
    """One card, and what a run that stopped left in the store."""
    (one,) = seeded(database, card(**overrides))
    result = write_problems(
        model,
        CallLog(database),
        one,
        one.templates[0],
        Corpus.at(database),
        drafts=drafts,
        outcomes=OutcomeLog(database),
    )
    return one, result


def test_a_resume_ends_on_the_row_a_writing_ends_on(database, monkeypatch):
    """A resumed draft's stage lines otherwise stop at its last step, and
    whether it landed is readable only once the whole sweep is over."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held
    seen: list[Progress] = []

    resume(
        FakeWriter(generator=BUILDS, slow=SLOW),
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        drafts=drafts,
        on_progress=seen.append,
    )

    (row,) = seen
    assert row.landed
    assert row.title == stopped.draft.title
    assert row.separating is not None


def test_a_resumed_draw_separates_where_the_stored_naive_solution_did_not(database, monkeypatch):
    """The exit a held draft takes where nothing was wrong with the run: the
    site is asked again and this answer is slow."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held
    assert stopped.draft.state is WritingState.SEARCHED
    model = FakeWriter(generator=BUILDS, slow=SLOW)

    result = resume(
        model,
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        drafts=drafts,
    )

    asked = [call["system"] for call in model.calls]
    assert asked == [naive.SYSTEM]
    assert result.started_at is WritingState.PACED
    assert len(result.drafted) == 1


def test_a_redrawn_naive_solution_carries_the_size_its_search_found(database, monkeypatch):
    """The input generator was reused, so the inputs site made no call and wrote
    no record. Filed nowhere, the size a resumed problem landed on would be
    readable only from the arguments of its own case."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held

    resume(
        FakeWriter(generator=BUILDS, slow=SLOW),
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        outcomes=OutcomeLog(database),
        drafts=drafts,
    )

    left = {one.site: one for one in OutcomeLog(database).outcomes() if one.problem_id}
    assert set(left) == {CallSite.NAIVE}
    assert left[CallSite.NAIVE].separating is not None


def test_a_moved_naive_solution_re_pays_that_call_and_no_other(database, monkeypatch):
    """The reference and the input generator are written from the statement,
    which this bench did not move."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held
    model = FakeWriter(generator=BUILDS, slow=SLOW)

    result = resume(
        model,
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        bench=BENCH.model_copy(update={"naive": OTHER}),
        drafts=drafts,
    )

    asked = [call["system"] for call in model.calls]
    assert naive.SYSTEM in asked
    assert blind.SYSTEM not in asked and inputs.SYSTEM not in asked
    assert result.started_at is WritingState.PACED
    # the new naive separated where the stored one did not, so the draft lands
    assert len(result.drafted) == 1


def test_a_resume_pays_for_the_step_that_had_no_answer_and_no_other(database, monkeypatch):
    """The draft holds the reference the first run bought, so the resume is
    charged for the input generator alone."""
    monkeypatch.setattr("algo_coach.generation.timing.DRILL_CAP_MS", 60)
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(slow=SLOW), drafts, templates=CLAIMED)
    (stopped,) = first.held
    stages: list[str] = []
    model = FakeWriter(slow=SLOW, generator=BUILDS)

    result = resume(
        model,
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        notes=Notes(lambda step: stages.append(f"{step.name}: {step.detail}")),
        drafts=drafts,
    )

    assert result.started_at is WritingState.BUILT
    assert "resume: starting at built" in stages
    assert blind.SYSTEM not in [asked["system"] for asked in model.calls]
    assert len(result.drafted) == 1
    # cleared, since the problem it became is what a reader finds
    assert drafts.all() == []


def test_a_draft_a_raised_call_left_resumes_at_that_call(database):
    """The steps before it stand, and the one that answered nothing is where
    the resume starts."""
    drafts = DraftStore(database)
    one, first = written(database, Raises(), drafts)
    (stopped,) = first.held
    assert stopped.draft.state is WritingState.CHECKED

    result = resume(
        FakeWriter(),
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        drafts=drafts,
    )

    assert result.started_at is WritingState.REFERENCED
    assert len(result.drafted) == 1


def test_a_resumed_step_writes_a_second_site_outcome(database):
    """Never an amendment, as a re-run of any site over one item does. Both
    group under the writing id the draft carries."""
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held

    resume(
        FakeWriter(generator=BUILDS),
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        bench=BENCH.model_copy(update={"blind": OTHER}),
        outcomes=OutcomeLog(database),
        drafts=drafts,
    )

    read = [left for left in OutcomeLog(database).outcomes() if left.site is CallSite.BLIND]
    assert [left.model for left in read] == [BENCH.blind.model, OTHER.model]
    assert {left.writing_id for left in read} == {stopped.draft.id}


def test_a_resume_that_holds_again_leaves_the_draft_where_it_stopped(database):
    """Forward only: the local steps run again, and a draft moved back would
    re-pay the calls it holds if the run then died."""
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held

    result = resume(
        FakeWriter(generator=BUILDS),
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        drafts=drafts,
    )

    (again,) = result.held
    assert again.draft.state is WritingState.SEARCHED
    assert drafts.get(stopped.draft.id).state is WritingState.SEARCHED


def test_a_moved_blind_configuration_re_pays_no_input_generator(database):
    """Both prompts are the statement alone, so neither site invalidates the
    other."""
    drafts = DraftStore(database)
    one, first = written(database, FakeWriter(generator=BUILDS), drafts, templates=CLAIMED)
    (stopped,) = first.held
    model = FakeWriter(generator=BUILDS)

    result = resume(
        model,
        CallLog(database),
        Target(card=one, template=one.templates[0]),
        stopped.draft,
        Corpus.at(database),
        bench=BENCH.model_copy(update={"blind": OTHER}),
        drafts=drafts,
    )

    asked = [call["system"] for call in model.calls]
    assert blind.SYSTEM in asked
    assert inputs.SYSTEM not in asked
    (again,) = result.held
    assert again.draft.inputs_provenance == stopped.draft.inputs_provenance


def test_a_rejected_draft_is_not_resumed(database):
    """Its gate said the answer was wrong, so a resume skipping that gate would
    land what the gate rejected."""
    drafts = DraftStore(database)
    one, _ = written(database, FakeWriter(canonical=WRONG), drafts)
    (gated,) = drafts.all()

    with pytest.raises(ValueError, match="rejected"):
        resume(FakeWriter(), CallLog(database), one.templates[0], gated, Corpus.at(database))


def test_a_moved_margin_re_enters_the_search(database):
    """The share of the cap the canonical may take is a constant like the
    ceiling, and a draft held on it waits for exactly that number to move."""
    stopped = at_ceiling(database, "canonical_too_slow", CEILING, margin=MARGIN * 2)

    assert moved_at(stopped, CLAIMS, BENCH) is WritingState.SEARCHED


def test_a_moved_count_bound_re_enters_the_search(database):
    """A count the bound cut short is a walk that stopped early, and raising
    the bound is what lets it reach the cap."""
    stopped = at_ceiling(database, "input_too_large", CEILING, repeats_max=REPEATS_MAX // 2)

    assert moved_at(stopped, CLAIMS, BENCH) is WritingState.SEARCHED


def test_the_free_step_is_taken_before_the_paid_one(database):
    """A draft held on the canonical's margin can both re-walk and draw the
    naive site again, and the search costs subprocesses where a draw costs a
    call."""
    stopped = at_ceiling(database, "canonical_too_slow", CEILING // 4)

    assert moved_at(stopped, CLAIMS, BENCH) is WritingState.SEARCHED


def test_a_draft_held_on_the_margin_draws_again_where_no_bound_moved(database):
    """Nothing else releases it: the two solutions ran within a constant factor
    and the sampled site is the one that can answer differently."""
    stopped = at_ceiling(database, "canonical_too_slow", CEILING)

    assert moved_at(stopped, CLAIMS, BENCH) is WritingState.PACED


def test_a_changed_search_re_enters_it(database):
    """A bound the draft records moves with the ceiling and the margin, and not
    with the walk itself. The revision is what a change to the walk moves."""
    stopped = at_ceiling(database, "case_too_large", CEILING, search_revision=SEARCH_REVISION - 1)

    assert moved_at(stopped, CLAIMS, BENCH) is WritingState.SEARCHED
