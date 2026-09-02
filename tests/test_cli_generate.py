"""The generate command: a template in, problems out, and each one stored once
its runs kept it."""

from importlib import import_module

import pytest
from generating import FakeWriter
from matching import card, seeded, template

from algo_coach import cli
from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cases import CaseLog
from algo_coach.cli.generate import verdict
from algo_coach.generation import MODEL, Progress
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import CaseOutcome, MatchSource, SolutionRole
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
    assert "The first." in out and "The second." in out
    assert f"2 problem(s) stored, written by {MODEL}" in out
    assert len(CallLog(root).all()) == 4


def test_a_problem_its_runs_kept_is_stored_whole(root, monkeypatch, capsys):
    """A problem lands once its canonical has passed and the reference has
    agreed with it."""
    run(monkeypatch, FakeWriter(), "longest-valid-window")

    (problem,) = ProblemStore(root).all()
    assert problem.statement == "A statement."
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


def test_the_canonical_is_printed_only_when_asked_for(root, monkeypatch, capsys):
    run(monkeypatch, FakeWriter(), "longest-valid-window", "--code")

    assert "def solve(xs):" in capsys.readouterr().out


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
    assert "nothing written" in capsys.readouterr().err


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
    """A run aimed by the gap report rather than at a template named by hand."""
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
    """The report names the templates, so the two would contradict each other."""
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
