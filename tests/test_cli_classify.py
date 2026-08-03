from importlib import import_module

import pytest
from helpers import FakeClient, Verdict, attempt, seed_problem

from algo_coach import cli
from algo_coach.claims import MODEL
from algo_coach.log import AttemptLog

# By module, not by dotted string: `algo_coach.cli.classify` resolves to the
# command the package re-exports, which shadows the module of the same name.
COMMAND = import_module("algo_coach.cli.classify")


def run(monkeypatch, client: FakeClient, *argv: str) -> None:
    monkeypatch.setattr(COMMAND, "Anthropic", lambda: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "classify", "--user", "u1", *argv])
    cli.main()


@pytest.fixture
def root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    seed_problem(data, id="two-tags", tags=["Greedy", "Sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    AttemptLog(data).append_attempt(attempt("a1", "two-tags"))
    return data


def test_the_command_claims_the_backlog(root, monkeypatch, capsys):
    run(monkeypatch, FakeClient.answering(Verdict(["greedy"])))

    (claim,) = AttemptLog(root).claims()
    assert claim.techniques == ["greedy"]
    assert f"1 claim(s) written by {MODEL}" in capsys.readouterr().out


def test_a_run_that_landed_nothing_exits_nonzero(root, monkeypatch, capsys):
    """A key that does not work fails every attempt in turn — silence and a
    zero exit would read as a backlog with nothing left to claim."""
    client = FakeClient.answering(Verdict(error=RuntimeError("bad key")))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, client)

    assert exit_info.value.code == 1
    assert "bad key" in capsys.readouterr().out


def test_the_limit_caps_the_run(root, monkeypatch, capsys):
    AttemptLog(root).append_attempt(attempt("a2", "two-tags"))
    client = FakeClient.answering(Verdict(["greedy"]))

    run(monkeypatch, client, "--limit", "1")

    assert len(client.messages.calls) == 1
    assert len(AttemptLog(root).claims()) == 1
