from generating import NAIVE, FakeWriter
from helpers import PROVENANCE
from matching import card, seeded, template

from algo_coach.calls import CallLog, Configuration
from algo_coach.cases import CaseLog
from algo_coach.drafts import DraftStore
from algo_coach.generation import (
    BENCH,
    GENERATOR_DEFAULT,
    Bench,
    Corpus,
    Progress,
    blind,
    clock,
    discrimination,
    generator,
    inputs,
    write_problems,
)
from algo_coach.generation import run as run_module
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import ExpectedSource, Problem, WritingState


def run(tmp_path, model: FakeWriter, *, count: int = 1):
    (one,) = seeded(tmp_path, card())
    return one, write_problems(
        model, CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path), count=count
    )


def test_a_problem_takes_three_calls_in_one_order(tmp_path):
    """The reference and the input generator are both written from the
    statement, so neither can be asked for before there is one."""
    model = FakeWriter()

    _, result = run(tmp_path, model)

    assert [one["system"] for one in model.calls] == [generator.SYSTEM, blind.SYSTEM, inputs.SYSTEM]
    assert len(result.drafted) == 1
    assert result.drafted[0].reference.startswith("def solve")


def test_each_call_is_shown_what_the_run_wrote_before_it(tmp_path):
    """Added without waiting for the problem to land, or a run of ten writes
    ten problems against one list."""
    model = FakeWriter(statements=["The first.", "The second."])

    run(tmp_path, model, count=2)

    assert "The first." not in model.briefs[0]
    assert "The first." in model.briefs[1]


def test_the_corpus_seeds_the_list(tmp_path):
    """What a form already carries is what the first call has to differ
    from."""
    (one,) = seeded(tmp_path, card())
    corpus = Corpus.at(tmp_path)
    corpus.problems.put(
        Problem(
            id="p1",
            title="p1",
            statement="An earlier statement.",
            generated_for=one.templates[0].id,
            **PROVENANCE,
        )
    )
    model = FakeWriter()

    write_problems(model, CallLog(tmp_path), one, one.templates[0], corpus)

    assert "An earlier statement." in model.briefs[0]


def test_a_failure_costs_one_problem(tmp_path):
    """A refusal or a reply that does not parse is this problem's, and the run
    behind it still writes."""
    model = FakeWriter(statements=[None, "The second."])

    _, result = run(tmp_path, model, count=2)

    assert [one.index for one in result.failed] == [1]
    assert len(result.drafted) == 1
    assert not result.aborted


def test_several_failures_in_a_row_end_the_run(tmp_path):
    """Consecutive failures mean the configuration is broken rather than the
    model unlucky."""
    model = FakeWriter(statements=[None])

    _, result = run(tmp_path, model, count=ABORT_AFTER + 2)

    assert result.aborted
    assert len(result.failed) == ABORT_AFTER


def test_every_call_is_recorded(tmp_path):
    """Every one, the failed one included: what a run paid for stays readable
    whatever it produced. One problem failed at its first call, and the other
    took three."""
    model = FakeWriter(statements=[None, "The second."])

    run(tmp_path, model, count=2)

    assert len(CallLog(tmp_path).all()) == 4


def test_a_problem_the_runs_reject_is_reported_apart(tmp_path):
    """A written problem can still be discarded, and a report folding the two
    would say a call refused where the model wrote and the runs rejected."""
    model = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n")

    _, result = run(tmp_path, model)

    assert result.drafted == []
    assert result.failed == []
    assert [one.discard for one in result.discarded] == ["disagreed"]
    assert "disagree on 1 case(s)" in result.discarded[0].reason


def test_a_discard_does_not_end_the_run(tmp_path):
    """`ABORT_AFTER` catches a broken configuration. Every call answered here,
    and what the runs rejected is the model's writing."""
    model = FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n")

    _, result = run(tmp_path, model, count=ABORT_AFTER + 1)

    assert not result.aborted
    assert len(result.discarded) == ABORT_AFTER + 1


def test_a_discarded_statement_is_still_shown_to_the_next_call(tmp_path):
    """It was written for this form, and asking for it again is what the list
    exists to prevent."""
    model = FakeWriter(
        statements=["The first.", "The second."],
        solution="def solve(xs):\n    return len(xs) + 1\n",
    )

    run(tmp_path, model, count=2)

    assert "The first." in model.briefs[1]


def test_a_surviving_problem_carries_what_the_reference_computed(tmp_path):
    """The draft's own values were the gate. What would land is the answer the
    independent solution gave, and the case names it."""
    _, result = run(tmp_path, FakeWriter())

    (drafted,) = result.drafted
    assert [one.expected for one in drafted.cases] == [3]
    assert [one.expected_from for one in drafted.cases] == [ExpectedSource.REFERENCE]


SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"
BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"


def claiming(overrides: dict) -> dict:
    """A card whose template claims a speedup, which is what the search is run
    for and what holds the draft where nothing separated."""
    return {"templates": [template("longest-valid-window", speedup=True)]} | overrides


def timed(tmp_path, monkeypatch, model: FakeWriter, **overrides):
    """A run whose sitting cap is small enough to separate in a test, over a
    template claiming the speedup that makes the search run."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    (one,) = seeded(tmp_path, card(**claiming(overrides)))
    return one, write_problems(model, CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path))


def test_the_separating_case_is_stored_beside_the_others(tmp_path, monkeypatch):
    """A submission is judged at that size, so the naive solution the form
    replaces fails the problem."""
    model = FakeWriter(solution=SLOW, generator=BUILDS)

    timed(tmp_path, monkeypatch, model)

    stored = CaseLog(tmp_path).cases()
    assert [one.args for one in stored] == [[[1, 2, 3]], [[0, 1]]]
    assert stored[-1].expected_from is ExpectedSource.REFERENCE


def test_the_mutation_loop_never_sees_the_separating_case(tmp_path, monkeypatch):
    """The survivors are decided against the set as the statement left it, so
    the case the search won cannot be in it whichever ran first."""
    seen: list[list] = []
    loop = run_module.harden

    def capture(*args, cases, **kwargs):
        seen.append([one.args for one in cases])
        return loop(*args, cases=cases, **kwargs)

    monkeypatch.setattr("algo_coach.generation.run.harden", capture)

    timed(tmp_path, monkeypatch, FakeWriter(solution=SLOW, generator=BUILDS))

    assert seen == [[[[1, 2, 3]]]]
    assert [one.args for one in CaseLog(tmp_path).cases()] == [[[1, 2, 3]], [[0, 1]]]


def test_a_form_that_is_its_own_optimum_is_still_built_for(tmp_path, monkeypatch):
    """Backtracking and exhaustive search have no naive solution to beat, so
    nothing is searched for. The input generator is written all the same, since
    a fuzz pass has no inputs without one."""
    model = FakeWriter(solution=SLOW, generator=BUILDS)

    timed(
        tmp_path,
        monkeypatch,
        model,
        templates=[template("longest-valid-window", speedup=False)],
    )

    assert [one["system"] for one in model.calls] == [generator.SYSTEM, blind.SYSTEM, inputs.SYSTEM]
    assert len(CaseLog(tmp_path).cases()) == 1


CRASHES = "def solve(size, seed):\n    raise ValueError\n"


def reported(tmp_path, monkeypatch, model: FakeWriter, **overrides) -> Progress:
    """The line one problem left, which is where a site's failure is read."""
    seen: list[Progress] = []
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    (one,) = seeded(tmp_path, card(**claiming(overrides)))
    write_problems(
        model,
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        on_progress=seen.append,
    )
    (line,) = seen
    return line


def test_a_builder_that_fails_holds_a_draft_claiming_a_speedup(tmp_path, monkeypatch):
    """No code to build with, so no search, so nothing demonstrates the claim.
    A landed problem is repaired nowhere, which is why the draft stops at the
    step the call failed before."""
    model = FakeWriter(solution=SLOW)

    _, result = timed(tmp_path, monkeypatch, model)

    (one,) = result.held
    assert one.draft.state is WritingState.AGREED
    assert one.unbuilt is not None
    assert (result.drafted, CaseLog(tmp_path).cases()) == ([], [])


def test_a_builder_that_fails_lands_a_form_that_is_its_own_optimum(tmp_path, monkeypatch):
    """Nothing was searched for, so the case the call cost was never one the
    problem needed."""
    model = FakeWriter(solution=SLOW)

    _, result = timed(
        tmp_path,
        monkeypatch,
        model,
        templates=[template("longest-valid-window", speedup=False)],
    )

    assert len(result.drafted) == 1
    assert len(CaseLog(tmp_path).cases()) == 1


def test_a_call_that_wrote_no_builder_is_reported_apart_from_a_search(tmp_path, monkeypatch):
    """A site that answered nothing and a search that separated nothing are
    different facts, and the fuzz pass is lost only by the first."""
    unwritten = reported(tmp_path, monkeypatch, FakeWriter(solution=SLOW))
    crashing = reported(tmp_path, monkeypatch, FakeWriter(solution=SLOW, generator=CRASHES))

    assert unwritten.unbuilt is not None
    assert unwritten.unseparated is None
    assert crashing.unbuilt is None
    assert "built nothing at size 1" in crashing.unseparated


def test_two_solutions_disagreeing_at_the_separating_size_discard_the_problem(
    tmp_path, monkeypatch
):
    """A canonical correct on the small cases and wrong at scale, which only
    the separating input reaches."""
    blind_solution = (
        "import time\n\n\ndef solve(xs):\n"
        "    time.sleep(len(xs) * 0.04)\n"
        "    return len(xs) + (1 if 0 in xs else 0)\n"
    )
    model = FakeWriter(solution=blind_solution, generator=BUILDS)

    _, result = timed(tmp_path, monkeypatch, model)

    assert result.drafted == []
    assert [one.discard for one in result.discarded] == ["disagreed"]
    assert CaseLog(tmp_path).cases() == []


def test_the_clock_is_written_between_the_builder_and_the_search(tmp_path, monkeypatch):
    """The builder is written for every problem, since the fuzz pass builds its
    inputs with it, and the search measures against what this step writes."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    (one,) = seeded(tmp_path, card(**claiming({})))
    stages: list[str] = []

    write_problems(
        FakeWriter(solution=SLOW, generator=BUILDS),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        on_step=lambda step: stages.append(step.name),
    )

    assert stages.index("inputs") < stages.index("clock") < stages.index("timing")


def test_a_form_that_is_its_own_optimum_pays_for_no_clock(tmp_path):
    """Nothing measures a solution the naive approach does not beat, so the
    site is asked exactly where the search is run."""
    (one,) = seeded(tmp_path, card())
    model = FakeWriter(generator=BUILDS)

    write_problems(model, CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path))

    assert clock.SYSTEM not in [asked["system"] for asked in model.calls]


def test_a_clock_that_was_not_written_holds_the_draft(tmp_path):
    """The search has nothing to measure the canonical against, so the draft
    stops here rather than landing undemonstrated."""
    (one,) = seeded(tmp_path, card(**claiming({})))
    drafts = DraftStore(tmp_path)

    result = write_problems(
        FakeWriter(generator=BUILDS, slow=None),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=drafts,
    )

    (held,) = result.held
    assert held.unpaced is not None
    assert held.draft.state is WritingState.BUILT
    assert held.draft.naive is None


def test_a_written_clock_is_held_on_the_draft(tmp_path):
    """A resume re-deriving it would re-pay the call, so the code and the
    configuration it was written at are both stored."""
    (one,) = seeded(tmp_path, card(**claiming({})))
    drafts = DraftStore(tmp_path)

    write_problems(
        FakeWriter(generator=BUILDS),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        drafts=drafts,
    )

    (stored,) = drafts.all()
    assert stored.state is WritingState.SEARCHED
    assert stored.naive == NAIVE
    assert stored.clock.model == BENCH.clock.model


def test_the_search_runs_before_the_mutation_loop(tmp_path, monkeypatch):
    """A canonical wrong at scale discards the problem, and the loop is what
    that saves: a round is paid for after the search rather than before it."""
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    (one,) = seeded(tmp_path, card(**claiming({})))
    stages: list[str] = []

    write_problems(
        FakeWriter(solution=SLOW, generator=BUILDS),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        on_step=lambda step: stages.append(step.name),
    )

    assert stages.index("timing") < stages.index("mutants")


# the mutation loop's subject: a boundary the one written case never reaches
BOUNDED = "def solve(n):\n    return n > 3\n"
BOUNDED_BLIND = "def solve(n):\n    return not n <= 3\n"
ONE_CASE = [{"args": "[10]", "expected": "true"}]


def bounded(**overrides) -> FakeWriter:
    written = {"canonical": BOUNDED, "solution": BOUNDED_BLIND, "cases": ONE_CASE}
    return FakeWriter(**(written | overrides))


def test_the_cases_the_mutation_loop_wins_land_with_the_others(tmp_path):
    """A submission is judged by them, which is what measures the set against
    the bound rather than against the generator's own judgement."""
    model = bounded(separators=[[[3], [4]]])

    _, result = run(tmp_path, model)

    assert len(result.drafted) == 1
    assert [one.args for one in CaseLog(tmp_path).cases()] == [[10], [3], [4]]


def test_a_proposal_that_killed_nothing_never_reaches_the_store(tmp_path):
    """The first run stored fifteen that killed nothing, and every later
    verification would run them."""
    model = bounded(separators=[[[100], [3], [4]]])

    run(tmp_path, model)

    assert [one.args for one in CaseLog(tmp_path).cases()] == [[10], [3], [4]]


def test_a_won_case_carries_the_reference_s_answer(tmp_path):
    """Settled as the first set is: a case the canonical produced would pass by
    construction."""
    run(tmp_path, bounded(separators=[[[3]]]))

    stored = CaseLog(tmp_path).cases()
    assert stored[-1].expected is False
    assert stored[-1].expected_from is ExpectedSource.REFERENCE


def test_the_input_generator_is_written_before_the_rounds(tmp_path):
    """A fuzz pass kills mutants with the inputs it builds, and a round is then
    paid for the survivors alone."""
    model = bounded(separators=[[[3], [4]]], generator=BUILDS)

    run(tmp_path, model)

    assert [one["system"] for one in model.calls] == [
        generator.SYSTEM,
        blind.SYSTEM,
        inputs.SYSTEM,
        discrimination.SYSTEM,
    ]


def test_a_builder_that_failed_costs_the_inputs_and_not_the_round(tmp_path):
    """The call says nothing about the statement, so the loop still runs and
    the problem still lands."""
    model = bounded(separators=[[[3], [4]]])

    _, result = run(tmp_path, model)

    assert len(result.drafted) == 1
    assert [one.args for one in CaseLog(tmp_path).cases()] == [[10], [3], [4]]


# one argument per pair, so the fuzz grid reaches the boundary `BOUNDED` turns
# on
COUNTS = "def solve(size, seed):\n    return [size + seed]\n"


def test_the_fuzz_pass_kills_what_a_round_would_have_been_paid_for(tmp_path):
    """The inputs cost subprocesses where a round costs a call, so a mutant the
    pass reaches is never asked about."""
    model = bounded(separators=[[[3], [4]]], generator=COUNTS)

    _, result = run(tmp_path, model)

    assert len(result.drafted) == 1
    assert discrimination.SYSTEM not in [one["system"] for one in model.calls]


def test_what_the_fuzz_pass_kept_lands_with_the_others(tmp_path):
    """A submission is judged by them, and the first round's survivors were
    decided against them, which is what `round` zero names."""
    model = bounded(separators=[[[3], [4]]], generator=COUNTS)

    run(tmp_path, model)

    stored = CaseLog(tmp_path).cases()
    assert [one.args for one in stored[1:]] == [[3], [4]]
    assert {one.round for one in stored} == {0}


def test_a_set_that_kills_every_mutant_pays_for_no_round(tmp_path):
    """Nothing survived the cases the generation call wrote, so no case has to
    exist."""
    model = FakeWriter()

    run(tmp_path, model)

    assert [one["system"] for one in model.calls] == [generator.SYSTEM, blind.SYSTEM, inputs.SYSTEM]


def test_a_round_that_fails_holds_the_draft_for_a_resume(tmp_path):
    """The problem passed every gate that judges it and its set was never
    measured against the bound, so the loop is asked again rather than the set
    stored as it stands."""
    reported: list = []
    (one,) = seeded(tmp_path, card())

    result = write_problems(
        bounded(),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        on_progress=reported.append,
    )

    (one,) = result.held
    # no input generator was written for it either, so it stopped a step
    # earlier
    assert one.draft.state is WritingState.AGREED
    assert one.unmeasured is not None
    assert (result.drafted, CaseLog(tmp_path).cases()) == ([], [])
    assert reported[0].unmeasured is not None


def test_a_proposed_case_the_two_solutions_answer_differently_discards_it(tmp_path):
    """A canonical wrong at a boundary the first set never reached, which is
    what the loop exists to find."""
    model = bounded(
        solution="def solve(n):\n    return 99 if n == 4 else n > 3\n",
        separators=[[[4]]],
    )

    _, result = run(tmp_path, model)

    assert result.drafted == []
    assert [one.discard for one in result.discarded] == ["disagreed"]
    assert CaseLog(tmp_path).cases() == []


def test_a_run_reports_every_stage_as_it_goes(tmp_path):
    """What the run is waiting on, and what each call cost. A problem takes
    minutes, and the line per problem prints when it is over."""
    reported: list = []
    (one,) = seeded(tmp_path, card())

    write_problems(
        bounded(separators=[[[3], [4]]]),
        CallLog(tmp_path),
        one,
        one.templates[0],
        Corpus.at(tmp_path),
        on_step=reported.append,
    )

    assert [step.name for step in reported][:5] == [
        "statement",
        "statement",
        "cases",
        "reference",
        "reference",
    ]
    assert "mutants" in [step.name for step in reported]
    assert [step.call for step in reported].count(None) < len(reported)


def models(model: FakeWriter) -> dict[str, str]:
    """Which model each call site was asked of, by the brief it was sent."""
    named = {
        generator.SYSTEM: "generator",
        blind.SYSTEM: "blind",
        discrimination.SYSTEM: "discrimination",
        inputs.SYSTEM: "inputs",
    }
    return {named[one["system"]]: one["model"] for one in model.calls}


def test_every_site_is_asked_of_its_own_model(tmp_path):
    """Four calls asking for different things, where one configuration made
    the cheapest of them pay the price of the hardest."""
    bench = Bench(
        generator=Configuration(model="writes-problems", effort="medium", pin="test"),
        blind=Configuration(model="reads-statements", effort="medium", pin="test"),
        discrimination=Configuration(model="writes-cases", effort="medium", pin="test"),
        inputs=Configuration(model="builds-inputs", effort="medium", pin="test"),
    )
    model = bounded(separators=[[[3], [4]]], generator=BUILDS)
    (one,) = seeded(tmp_path, card())

    write_problems(
        model, CallLog(tmp_path), one, one.templates[0], Corpus.at(tmp_path), bench=bench
    )

    assert models(model) == {
        "generator": "writes-problems",
        "blind": "reads-statements",
        "discrimination": "writes-cases",
        "inputs": "builds-inputs",
    }


def test_a_run_naming_no_bench_asks_one_model(tmp_path):
    """The bench a run was given none of is the run that ran before there was
    one."""
    model = bounded(separators=[[[3], [4]]], generator=BUILDS)

    run(tmp_path, model)

    assert set(models(model).values()) == {GENERATOR_DEFAULT.model}
