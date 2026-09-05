from datetime import UTC, datetime
from importlib import import_module

import pytest
from generating import FakeWriter, Raises
from matching import card, seeded, template

from algo_coach import cli
from algo_coach.calls import CallLog, Configuration
from algo_coach.cards import CardStore
from algo_coach.cases import CaseLog
from algo_coach.cli.generate import staged, summary, verdict
from algo_coach.drafts import DraftStore
from algo_coach.generation import (
    BENCH,
    DISCRIMINATION_DEFAULT,
    GENERATOR_DEFAULT,
    Bench,
    Progress,
    Step,
    blind,
    discrimination,
    generator,
    inputs,
    reject,
)
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Call, CaseOutcome, MatchSource, SolutionRole
from algo_coach.solutions import SolutionLog

TRANSPORT = import_module("algo_coach.cli.transport")


def run(monkeypatch, model: FakeWriter, *argv: str) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: model)
    monkeypatch.setattr(
        "sys.argv",
        ["algo-coach", "generate", "--card", "sliding-window", "--template", *argv],
    )
    cli.main()


@pytest.fixture
def root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    seeded(data, card())
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    return data


def test_the_command_writes_problems(root, monkeypatch, capsys):
    model = FakeWriter(statements=["The first.", "The second."])

    run(monkeypatch, model, "longest-valid-window", "--count", "2")

    out = capsys.readouterr().out
    assert "2 problem(s) stored, written by" in out
    assert f"generator {GENERATOR_DEFAULT.model} at {GENERATOR_DEFAULT.effort}" in out
    assert len(CallLog(root).all()) == 6


def test_the_run_names_each_stored_problem_and_not_its_statement(root, monkeypatch, capsys):
    """Ten statements scroll the result out of the terminal, and the id is what
    reads one whole."""
    model = FakeWriter(statements=["The first.", "The second."])

    run(monkeypatch, model, "longest-valid-window", "--count", "2")

    out = capsys.readouterr().out
    assert "The first." not in out and "The second." not in out
    assert "# stored" in out
    for problem in ProblemStore(root).all():
        assert f"{problem.id}  {problem.title}" in out


def test_the_run_reports_what_its_calls_cost(root, monkeypatch, capsys):
    """A run's own tail rather than the whole log: the store is what a later
    query reads, and this is what one sitting spent."""
    run(monkeypatch, FakeWriter(), "longest-valid-window")

    assert "3 call(s), 0 output token(s)" in capsys.readouterr().out


def test_a_problem_its_runs_kept_is_stored_whole(root, monkeypatch, capsys):
    """A problem lands once its canonical has passed and the reference has
    agreed with it."""
    run(monkeypatch, FakeWriter(), "longest-valid-window")

    (problem,) = ProblemStore(root).all()
    # the signature the fixture appends: every statement carries the one its
    # cases pass, since three briefs read the order off it
    assert problem.statement.startswith("A statement.")
    assert problem.statement.endswith("def solve(xs)")
    assert [one.problem_id for one in CaseLog(root).cases()] == [problem.id]
    assert [one.role for one in SolutionLog(root).for_problem(problem.id)] == [
        SolutionRole.CANONICAL,
        SolutionRole.REFERENCE,
    ]
    canonical, _ = SolutionLog(root).for_problem(problem.id)
    assert [(one.solution_id, one.source) for one in MatchLog(root).matches()] == [
        (canonical.id, MatchSource.GENERATOR)
    ]


def test_a_discarded_problem_stores_nothing(root, monkeypatch, capsys):
    """Discarded whole rather than kept for repair, and the calls that wrote it
    stay in the log."""
    run(
        monkeypatch,
        FakeWriter(solution="def solve(xs):\n    return len(xs) + 1\n"),
        "longest-valid-window",
    )

    assert ProblemStore(root).all() == []
    assert CaseLog(root).cases() == []
    assert "1 discarded" in capsys.readouterr().out
    assert len(CallLog(root).all()) == 2


def test_an_unseeded_card_is_named_before_any_call(root, monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: FakeWriter())
    monkeypatch.setattr(
        "sys.argv",
        ["algo-coach", "generate", "--card", "monotonic-stack", "--template", "next-greater"],
    )

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "no card 'monotonic-stack'" in capsys.readouterr().err


def test_a_template_the_card_does_not_carry_names_the_ones_it_does(root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeWriter(), "next-greater")

    assert exit_info.value.code == 2
    err = capsys.readouterr().err
    assert "no template 'next-greater'" in err
    assert "longest-valid-window, fixed-window" in err


def test_a_run_that_wrote_nothing_exits_nonzero(root, monkeypatch, capsys):
    model = FakeWriter(statements=[None])

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, model, "longest-valid-window")

    assert exit_info.value.code == 1
    assert "no problem stored" in capsys.readouterr().err


def line(**fields) -> str:
    return verdict(Progress(index=1, total=1, template_slug="t", **fields))


def test_the_line_reports_the_case_run_and_whether_it_landed():
    """Apart, because a problem that survived its runs is stored by a later
    act, and a discarded one is the whole line instead."""
    assert line(cases=4, outcome=CaseOutcome.PASSED, landed=True) == "4 case(s)  passed  landed"
    assert line(cases=4, outcome=CaseOutcome.PASSED) == "4 case(s)  passed  not stored"


def test_a_discarded_problem_is_reported_by_its_gate():
    """The outcome says how the canonical ran, and the reason says why nothing
    was kept."""
    assert line(cases=4, outcome=CaseOutcome.WRONG, reason="discarded: x") == "! discarded: x"


def test_a_problem_nothing_ran_claims_no_landing():
    """The run is what decides landing, so a report before it says only that
    the cases have not been run."""
    assert line(cases=4) == "4 case(s)  not run"


def test_a_failure_is_the_whole_line():
    assert line(reason="RuntimeError('bad key')") == "! RuntimeError('bad key')"


def aimed(monkeypatch, model: FakeWriter, *argv: str) -> None:
    """A run aimed by the gap report rather than at a template named by
    hand."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: model)
    monkeypatch.setattr("sys.argv", ["algo-coach", "generate", "--gaps", *argv])
    cli.main()


def test_a_gap_run_writes_for_every_core_template(root, monkeypatch, capsys):
    """Both forms the seeded card carries, since nothing displays either."""
    model = FakeWriter(statements=["The first.", "The second."])

    aimed(monkeypatch, model)

    out = capsys.readouterr().out
    assert "2 problem(s) stored" in out and "over 2 template(s)" in out
    written = {one.generated_for for one in ProblemStore(root).all()}
    card = CardStore(root).by_slug("sliding-window")
    assert written == {one.id for one in card.templates}


def test_a_covered_form_is_not_written_again(root, monkeypatch, capsys):
    """One form is displayed already, so the run is aimed at what is left."""
    run(monkeypatch, FakeWriter(statements=["The first."]), "fixed-window")
    capsys.readouterr()

    aimed(monkeypatch, FakeWriter(statements=["The second."]))

    out = capsys.readouterr().out
    assert "1 problem(s) stored" in out and "template(s)" not in out
    written = [one.generated_for for one in ProblemStore(root).all()]
    assert len(set(written)) == 2


def test_a_corpus_with_no_gap_asks_for_nothing(root, monkeypatch, capsys):
    aimed(monkeypatch, FakeWriter(statements=["The first.", "The second."]))
    capsys.readouterr()

    with pytest.raises(SystemExit) as exit_info:
        aimed(monkeypatch, FakeWriter())

    assert exit_info.value.code == 0
    assert "no gap" in capsys.readouterr().err


def test_a_named_template_says_nothing_beside_gaps(root, monkeypatch, capsys):
    """The report names the templates, so the two would contradict each
    other."""
    with pytest.raises(SystemExit) as exit_info:
        aimed(monkeypatch, FakeWriter(), "--template", "fixed-window")

    assert exit_info.value.code == 2
    assert "--template says nothing" in capsys.readouterr().err


def test_a_run_names_a_template_or_aims_itself(root, monkeypatch, capsys):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: FakeWriter())
    monkeypatch.setattr("sys.argv", ["algo-coach", "generate", "--card", "sliding-window"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "name a --card and a --template" in capsys.readouterr().err


def test_a_card_narrows_what_the_gaps_aim_at(root, monkeypatch, capsys):
    """Every core template of one card, where the report covers the store."""
    seeded(root, card("union-find", technique="union-find", templates=[template("plain-union")]))

    aimed(
        monkeypatch,
        FakeWriter(statements=["The first.", "The second."]),
        "--card",
        "sliding-window",
    )

    assert "over 2 template(s)" in capsys.readouterr().out
    cards = {one.generated_for for one in ProblemStore(root).all()}
    assert len(cards) == 2


def test_the_line_reports_the_separating_size():
    """What a timing case was stored at, since a run that found none teaches
    the form without enforcing it."""
    landed = line(cases=4, outcome=CaseOutcome.PASSED, landed=True, separating=2048)

    assert landed == "4 case(s)  passed  landed  separates at 2048"


def test_a_form_that_separated_at_nothing_says_why():
    """A defect where the template claimed a speedup, so it is not silent."""
    landed = line(cases=4, outcome=CaseOutcome.PASSED, landed=True, unseparated="naive_finished")

    assert landed.endswith("no case: naive_finished")


def test_a_separation_proved_and_not_stored_is_not_read_as_a_stored_one():
    """The search reached a size and the case at it weighs too much, so the
    size is evidence the speedup holds rather than a case a sitting is judged
    by."""
    landed = line(
        cases=4,
        outcome=CaseOutcome.PASSED,
        landed=True,
        separating=4096,
        unseparated="case_too_large",
    )

    assert landed.endswith("no case at 4096: case_too_large")


def test_the_line_counts_what_the_generator_misdeclared():
    """It rejects nothing, so it prints beside the verdict: one call wrote the
    canonical and the declaration, and the reference is what decides a case."""
    landed = line(cases=9, outcome=CaseOutcome.PASSED, landed=True, misdeclared=2)

    assert landed == "9 case(s)  passed  landed  2 misdeclared"


def test_the_line_reports_what_the_problem_cost():
    """The stage lines price one call each, and the row is where the total for
    a problem nobody watched live is read."""
    landed = line(cases=4, outcome=CaseOutcome.PASSED, landed=True, cost=0.0123)

    assert landed.endswith("$0.0123")


def test_a_form_that_is_its_own_optimum_says_nothing():
    assert line(cases=4, outcome=CaseOutcome.PASSED, landed=True) == "4 case(s)  passed  landed"


def test_the_line_reports_what_the_mutation_loop_caught():
    """Which mistakes the stored set catches, since a survivor is a case the
    problem landed without."""
    landed = line(
        cases=4,
        outcome=CaseOutcome.PASSED,
        landed=True,
        mutants=12,
        survived=2,
        won=3,
        offered=18,
        declared=6,
        fuzzed=2,
        caught=[2],
    )

    assert landed == (
        "4 case(s)  passed  landed  kills 10/12 (6 set, 2 fuzz, 2 round 1), "
        "18 case(s) proposed, 3 landed"
    )


def test_the_line_reports_what_a_round_proposed_and_what_landed():
    """A proposal that killed nothing is not stored, and the two numbers are
    what says how much of the call was waste."""
    landed = line(
        cases=4,
        outcome=CaseOutcome.PASSED,
        landed=True,
        mutants=12,
        survived=2,
        won=3,
        offered=18,
        caught=[10],
    )

    assert landed.endswith("18 case(s) proposed, 3 landed")


def test_a_round_that_killed_nothing_still_prints_its_zero():
    """Whether a round earns its call is read from the split, and a source left
    out reads as one nobody tried."""
    landed = line(
        cases=4,
        outcome=CaseOutcome.PASSED,
        landed=True,
        mutants=12,
        survived=2,
        declared=10,
        caught=[0, 0],
    )

    assert "(10 set, 0 fuzz, 0 round 1, 0 round 2)" in landed


def test_a_set_no_round_measured_says_so():
    """A call that failed costs the round, and a line falling silent would read
    as a set the mutants could not beat."""
    landed = line(cases=4, outcome=CaseOutcome.PASSED, landed=True, unmeasured="no cases")

    assert landed.endswith("unmeasured: no cases")


def test_a_canonical_with_no_mutant_says_nothing():
    assert line(cases=4, outcome=CaseOutcome.PASSED, landed=True) == "4 case(s)  passed  landed"


def reported(**fields) -> str:
    return staged(Step(index=1, total=1, **fields))


def test_a_stage_line_names_what_is_happening():
    """A run reporting one line per problem shows nothing for the minutes the
    calls take."""
    assert reported(name="reference", detail="written") == "[1/1] reference  written"


def test_a_stage_that_paid_for_a_call_reports_what_it_cost():
    """Tokens and the wait are what a corpus is budgeted from, and the call log
    is not read while a run is going."""
    call = Call(
        id="c1",
        created_at=datetime(2026, 9, 3, tzinfo=UTC),
        model="m",
        effort="high",
        prompt="p",
        prompt_hash="h",
        response="{}",
        input_tokens=1200,
        output_tokens=3400,
        elapsed_ms=38_100,
        cost=0.0421,
    )

    assert reported(name="statement", detail="'A title'", call=call).endswith(
        "(1,200/3,400 tok, 38.1s, $0.0421)"
    )


def test_the_summary_names_one_model_where_every_site_shares_one():
    """A bench nobody mixed reads as one name rather than as a line per
    site."""
    one = GENERATOR_DEFAULT.model_copy(update={"temperature": 0.0})

    assert "written by " + one.model in summary(
        [], [], Bench(**dict.fromkeys(Bench.model_fields, one))
    )


def test_the_summary_names_how_each_site_was_sampled():
    """The built-in bench samples the generator and the clock and runs the rest
    greedy, and two sites on one model differ by nothing else a name shows."""
    named = summary([], [], BENCH)

    assert f"generator {GENERATOR_DEFAULT.model} at {GENERATOR_DEFAULT.effort} @default" in named
    assert f"clock {GENERATOR_DEFAULT.model} at {GENERATOR_DEFAULT.effort} @default" in named
    assert "blind " + GENERATOR_DEFAULT.model + " at " + GENERATOR_DEFAULT.effort + " @0.0" in named


def test_the_summary_names_every_site_where_the_bench_mixes_them():
    """A run that mixed models is unreadable as one name, and what wrote a
    problem is what a re-run has to name."""
    bench = Bench(discrimination=Configuration(model="cheap", effort="low", pin="test"))

    named = summary([], [], bench)

    assert "generator " + GENERATOR_DEFAULT.model in named
    assert "discrimination cheap at low" in named


BOUNDED = "def solve(n):\n    return 1 if n > 3 else 0\n"
BOUNDED_BLIND = "def solve(n):\n    return int(n > 3)\n"


def bounded(**overrides) -> FakeWriter:
    """A canonical with a boundary, so the mutation loop pays for a round and
    the discrimination site is reached."""
    written = {
        "canonical": BOUNDED,
        "solution": BOUNDED_BLIND,
        "cases": [{"args": "[10]", "expected": "1"}],
        "separators": [[[3], [4]]],
    }
    return FakeWriter(**(written | overrides))


def asked(model: FakeWriter) -> dict[str, dict]:
    """What each site was asked of, by the brief it was sent."""
    named = {
        generator.SYSTEM: "generator",
        blind.SYSTEM: "blind",
        discrimination.SYSTEM: "discrimination",
        inputs.SYSTEM: "inputs",
    }
    return {named[one["system"]]: one for one in model.calls}


def test_a_site_is_configured_alone(root, monkeypatch, capsys):
    """A cheaper model is tried on one call without an edit, and the other
    three keep the built-in configuration."""
    model = bounded()

    run(monkeypatch, model, "longest-valid-window", "--site", "discrimination", "--effort", "low")

    sites = asked(model)
    assert sites["discrimination"]["effort"] == "low"
    assert sites["generator"]["effort"] == GENERATOR_DEFAULT.effort
    assert "discrimination " + DISCRIMINATION_DEFAULT.model + " at low" in capsys.readouterr().out


def test_a_named_model_and_temperature_reach_their_site(root, monkeypatch):
    """Greedy is what makes a site's records comparable, and it is per site."""
    model = bounded()

    run(
        monkeypatch,
        model,
        "longest-valid-window",
        "--site",
        "blind",
        "--model",
        "another/model",
        "--provider",
        "somewhere",
        "--temperature",
        "0",
    )

    reference = asked(model)["blind"]
    assert (reference["model"], reference["pin"], reference["temperature"]) == (
        "another/model",
        "somewhere",
        0.0,
    )


def test_a_setting_before_any_site_is_refused(root, monkeypatch, capsys):
    """A model meant for one call would otherwise land on whichever site the
    list happens to open with."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeWriter(), "longest-valid-window", "--model", "cheap")

    assert exit_info.value.code == 2
    assert "name a --site" in capsys.readouterr().err


def test_a_model_from_elsewhere_needs_its_provider(root, monkeypatch, capsys):
    """An endpoint carries some models and not others, so an unpinned one is
    routed anywhere."""
    with pytest.raises(SystemExit) as exit_info:
        run(
            monkeypatch,
            FakeWriter(),
            "longest-valid-window",
            "--site",
            "blind",
            "--model",
            "another/model",
        )

    assert exit_info.value.code == 2
    assert "--provider needed" in capsys.readouterr().err


def test_one_site_named_twice_is_refused(root, monkeypatch):
    with pytest.raises(SystemExit) as exit_info:
        run(
            monkeypatch,
            FakeWriter(),
            "longest-valid-window",
            "--site",
            "blind",
            "--site",
            "blind",
        )

    assert exit_info.value.code == 2


def replaying(monkeypatch, model: FakeWriter, *argv: str) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: model)
    monkeypatch.setattr("sys.argv", ["algo-coach", "generate", "--replay", *argv])
    cli.main()


# what the input generator returns, so the site answers rather than failing
BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
# slow enough to separate at the cap the test lowers
SLOW = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) * 0.04)\n    return len(xs)\n"
ANOTHER = ("--site", "blind", "--model", "another", "--provider", "one")


def test_replay_pays_for_a_second_configuration_once(root, monkeypatch, capsys):
    """The corpus is the input, so a configuration reads a statement once. The
    run that wrote it already answers for the bench it was written with."""
    # a template claiming a speedup, so the inputs site has a pair to answer.
    # The problem then lands only where the search separated the two solutions
    monkeypatch.setattr("algo_coach.generation.run.DRILL_CAP_MS", 60)
    seeded(root, card(templates=[template("longest-valid-window", speedup=True)]))
    run(monkeypatch, FakeWriter(slow=SLOW, generator=BUILDS), "longest-valid-window")
    capsys.readouterr()

    replaying(monkeypatch, FakeWriter(generator=BUILDS), *ANOTHER)
    first = capsys.readouterr().out
    replaying(monkeypatch, FakeWriter(generator=BUILDS), *ANOTHER)
    second = capsys.readouterr().out

    assert "1 pair(s) asked, 2 skipped" in first
    assert "0 pair(s) asked, 3 skipped" in second


def test_replay_is_aimed_at_nothing(root, monkeypatch, capsys):
    """It reads the stored corpus, so the flags that aim a write name
    nothing."""
    with pytest.raises(SystemExit):
        replaying(monkeypatch, FakeWriter(), "--gaps")

    assert "aimed at nothing" in capsys.readouterr().err


CLAIMS = [template("longest-valid-window", speedup=True)]


def test_a_held_draft_is_named_by_the_template_and_what_stopped_it(root, monkeypatch, capsys):
    """A run's stage lines scroll past, and a held draft is the gap the next
    run is aimed at."""
    seeded(root, card(templates=CLAIMS))

    run(monkeypatch, FakeWriter(generator=BUILDS), "longest-valid-window")

    out = capsys.readouterr().out
    assert "# held" in out
    assert "longest-valid-window" in out and "searched" in out
    assert "no separating case: naive_finished" in out


def test_a_draft_held_before_the_search_names_the_step_that_answered_nothing(
    root, monkeypatch, capsys
):
    """No input generator was written, so the search never ran and the reason
    is not the one a search reports."""
    seeded(root, card(templates=CLAIMS))

    run(monkeypatch, FakeWriter(), "longest-valid-window")

    assert "no input generator" in capsys.readouterr().out


def test_the_summary_counts_the_held_apart_from_the_discarded(root, monkeypatch, capsys):
    """The calls a held draft paid for are kept, where a discarded one is
    lost."""
    seeded(root, card(templates=CLAIMS))

    run(monkeypatch, FakeWriter(generator=BUILDS), "longest-valid-window")

    out = capsys.readouterr().out
    assert "0 problem(s) stored" in out
    assert "1 held" in out


def test_a_draft_a_raised_call_left_is_named_too(root, monkeypatch, capsys):
    """The statement and the canonical are in the store, so a run reporting
    only that the call failed would read as a problem to write again."""
    seeded(root, card(templates=CLAIMS))

    with pytest.raises(SystemExit):
        run(monkeypatch, Raises(), "longest-valid-window")

    out, err = capsys.readouterr()
    assert "# held" in out and "checked" in out
    assert "the call raised: RuntimeError('the gateway is down')" in out
    assert "no problem stored" in err


def resuming(monkeypatch, model: FakeWriter, *argv: str) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: model)
    monkeypatch.setattr("sys.argv", ["algo-coach", "generate", "--resume", *argv])
    cli.main()


def held_draft(root, monkeypatch, capsys):
    """What a run whose blind call died leaves in the store."""
    with pytest.raises(SystemExit):
        run(monkeypatch, Raises(), "longest-valid-window")
    capsys.readouterr()
    (stored,) = DraftStore(root).all()
    return stored


def test_resume_carries_a_held_draft_forward(root, monkeypatch, capsys):
    """A prompt edit is spent on the drafts it repairs, where the library's
    resume was reachable from nothing."""
    held_draft(root, monkeypatch, capsys)

    resuming(monkeypatch, FakeWriter())

    out = capsys.readouterr().out
    assert "1 draft(s) resumed, 1 stored" in out
    assert "from 1 at referenced" in out
    assert len(ProblemStore(root).all()) == 1
    # cleared at landing, so the next resume finds nothing
    assert DraftStore(root).all() == []


def test_resume_reports_a_draft_that_is_held_again(root, monkeypatch, capsys):
    """The step it stopped at is what the next run aims at, so a resume that
    did not land it says so rather than falling silent."""
    held_draft(root, monkeypatch, capsys)

    with pytest.raises(SystemExit) as exit_info:
        resuming(monkeypatch, Raises())

    out = capsys.readouterr().out
    assert "1 held again" in out and "1 failed" in out
    assert exit_info.value.code == 1


def test_resume_skips_a_draft_naming_no_seeded_template(root, monkeypatch, capsys):
    """The form it was briefed on is gone, so nothing says what its search
    would be."""
    stored = held_draft(root, monkeypatch, capsys)
    DraftStore(root).put(stored.model_copy(update={"template_id": "gone"}))

    with pytest.raises(SystemExit):
        resuming(monkeypatch, FakeWriter())

    printed = capsys.readouterr()
    assert "no template gone" in printed.err
    assert "1 naming no template" in printed.out


def test_resume_with_no_draft_waiting_says_so(root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        resuming(monkeypatch, FakeWriter())

    assert exit_info.value.code == 0
    assert "no draft is waiting" in capsys.readouterr().err


def test_resume_is_aimed_at_nothing(root, monkeypatch, capsys):
    """It reads the stored drafts, so the flags that aim a write name
    nothing."""
    with pytest.raises(SystemExit):
        resuming(monkeypatch, FakeWriter(), "--gaps")

    assert "aimed at nothing" in capsys.readouterr().err


def test_a_replay_is_not_a_resume(root, monkeypatch, capsys):
    """One reads the corpus and the other the drafts, and a run doing both
    would report two things under one summary."""
    with pytest.raises(SystemExit) as exit_info:
        resuming(monkeypatch, FakeWriter(), "--replay")

    assert exit_info.value.code == 2
    assert "one at a time" in capsys.readouterr().err


def listing(monkeypatch, *argv: str) -> None:
    """No key and no transport: a listing names what a sweep would spend and
    spends none of it."""
    monkeypatch.setattr("sys.argv", ["algo-coach", "generate", "--drafts", *argv])
    cli.main()


def test_the_drafts_are_listed_with_the_step_each_would_resume_at(root, monkeypatch, capsys):
    """A sweep names what it will spend before it spends it."""
    stored = held_draft(root, monkeypatch, capsys)
    spent = len(CallLog(root).all())

    listing(monkeypatch)

    out = capsys.readouterr().out
    assert f"{stored.id}  longest-valid-window" in out
    assert "checked" in out and "starts at referenced" in out
    assert "1 draft(s) stored, 1 would resume" in out
    assert len(CallLog(root).all()) == spent


CRASHES = "def solve(size, seed):\n    raise ValueError\n"


def test_a_draft_no_resume_would_advance_is_listed_as_held(root, monkeypatch, capsys):
    """The builder crashed, so the search never ran and nothing about the bench
    moved. The step a resume would nominally start at is past the search, and
    the run holds the draft before reaching it."""
    seeded(root, card(templates=CLAIMS))
    run(monkeypatch, FakeWriter(generator=CRASHES), "longest-valid-window")
    capsys.readouterr()

    listing(monkeypatch)

    out = capsys.readouterr().out
    assert "starts at" not in out
    assert "held before the loop" in out and "built nothing at size 1" in out
    assert "1 draft(s) stored, 0 would resume" in out


def test_a_rejected_draft_is_counted_and_not_listed(root, monkeypatch, capsys):
    """Nothing resumes it, so a sweep's listing is what it will reach. The
    count still covers the store, or the summary would report fewer drafts than
    there are."""
    reject(DraftStore(root), held_draft(root, monkeypatch, capsys))

    listing(monkeypatch)

    out = capsys.readouterr().out
    assert "rejected by unexercised" not in out
    assert "1 draft(s) stored, 0 would resume" in out
    assert "1 rejected draft(s) not listed" in out


def test_the_rejected_drafts_are_listed_on_request(root, monkeypatch, capsys):
    """Its gate is readable nowhere else, so the listing is what prints it."""
    reject(DraftStore(root), held_draft(root, monkeypatch, capsys))

    listing(monkeypatch, "--all")

    out = capsys.readouterr().out
    assert "rejected by unexercised" in out
    assert "not listed" not in out


def test_a_listing_of_no_draft_says_so(root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        listing(monkeypatch)

    assert exit_info.value.code == 0
    assert "no draft is stored" in capsys.readouterr().err


def test_a_listing_is_aimed_at_nothing(root, monkeypatch, capsys):
    """It reads the stored drafts, as a resume does."""
    with pytest.raises(SystemExit) as exit_info:
        listing(monkeypatch, "--gaps")

    assert exit_info.value.code == 2
    assert "aimed at nothing" in capsys.readouterr().err


def reading(monkeypatch, wanted: str, *argv: str) -> None:
    """One stored draft, read whole. It makes no call, as a listing makes
    none."""
    monkeypatch.setattr("sys.argv", ["algo-coach", "generate", "--draft", wanted, *argv])
    cli.main()


def searched_draft(root, monkeypatch, capsys):
    """What the search leaves: every call answered, and no input separated the
    two solutions."""
    seeded(root, card(templates=CLAIMS))
    run(monkeypatch, FakeWriter(generator=BUILDS), "longest-valid-window")
    capsys.readouterr()
    (stored,) = DraftStore(root).all()
    return stored


def test_a_draft_is_read_whole_by_its_id(root, monkeypatch, capsys):
    """What a listing cannot hold: the statement, both solutions and the set
    the steps settled."""
    stored = searched_draft(root, monkeypatch, capsys)
    spent = len(CallLog(root).all())

    reading(monkeypatch, stored.id)

    out = capsys.readouterr().out
    assert f"# {stored.title} ({stored.id})" in out
    assert "longest-valid-window, medium, searched" in out
    assert stored.statement in out
    # the canonical, the reference, the builder and the clock
    assert out.count("```python") == 4
    assert f"## cases ({len(stored.cases)} settled, 0 won, 0 separating)" in out
    # the loop never ran, so the step that would have paid for it took nothing
    assert "discrimination  not taken" in out
    assert len(CallLog(root).all()) == spent


def test_the_sites_say_which_step_left_the_draft_where_it_is(root, monkeypatch, capsys):
    """The gate, the configuration behind it and the counters are readable
    nowhere else."""
    stored = searched_draft(root, monkeypatch, capsys)

    reading(monkeypatch, stored.id)

    out = capsys.readouterr().out
    assert "## sites" in out
    assert "unseparated: naive_finished" in out


def test_a_draft_is_named_by_a_prefix_of_its_id(root, monkeypatch, capsys):
    """An id is 32 hex characters, and a debugging read should not need all of
    them."""
    stored = searched_draft(root, monkeypatch, capsys)

    reading(monkeypatch, stored.id[:8])

    assert stored.statement in capsys.readouterr().out


def test_a_prefix_naming_two_drafts_is_refused(root, monkeypatch, capsys):
    """Reading whichever sorted first would answer about a draft nobody
    named."""
    stored = searched_draft(root, monkeypatch, capsys)
    drafts = DraftStore(root)
    drafts.put(stored.model_copy(update={"id": stored.id[:4] + "f" * 28}))

    with pytest.raises(SystemExit) as exit_info:
        reading(monkeypatch, stored.id[:4])

    assert exit_info.value.code == 2
    assert "names 2 drafts" in capsys.readouterr().err


def test_a_draft_that_is_not_stored_says_so(root, monkeypatch, capsys):
    with pytest.raises(SystemExit) as exit_info:
        reading(monkeypatch, "beef")

    assert exit_info.value.code == 1
    assert "no draft beef" in capsys.readouterr().err


def test_reading_a_draft_is_aimed_at_nothing(root, monkeypatch, capsys):
    """It names the draft it reads, as a listing reads them all."""
    stored = searched_draft(root, monkeypatch, capsys)

    with pytest.raises(SystemExit) as exit_info:
        reading(monkeypatch, stored.id, "--gaps")

    assert exit_info.value.code == 2
    assert "aimed at nothing" in capsys.readouterr().err
