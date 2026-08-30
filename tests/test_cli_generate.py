"""The generate command: a template in, problems out, and nothing stored until
they have been run."""

from importlib import import_module

import pytest
from generating import FakeWriter
from matching import card, seeded

from algo_coach import cli
from algo_coach.calls import CallLog
from algo_coach.cli.generate import verdict
from algo_coach.generation import MODEL, Progress
from algo_coach.problems import ProblemStore
from algo_coach.schema import CaseOutcome

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
    assert f"2 problem(s) written by {MODEL}" in out
    assert len(CallLog(root).all()) == 4


def test_nothing_is_stored_until_a_problem_has_been_run(root, monkeypatch, capsys):
    """A problem lands once its canonical has passed and the reference has
    agreed, and neither has run yet."""
    run(monkeypatch, FakeWriter(), "longest-valid-window")

    assert ProblemStore(root).all() == []
    assert "none stored" in capsys.readouterr().out


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
    """Apart, because a written problem can still be discarded: its canonical
    failing the cases, or the reference disagreeing with it."""
    assert line(cases=4, outcome=CaseOutcome.PASSED, landed=True) == "4 case(s)  passed  landed"
    assert line(cases=4, outcome=CaseOutcome.WRONG) == "4 case(s)  wrong  discarded"


def test_a_problem_nothing_ran_claims_no_landing():
    """The run is what decides landing, so a report before it says only that
    the cases have not been run."""
    assert line(cases=4) == "4 case(s)  not run"


def test_a_failure_is_the_whole_line():
    assert line(reason="RuntimeError('bad key')") == "! RuntimeError('bad key')"
