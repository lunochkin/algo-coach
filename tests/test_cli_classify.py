from importlib import import_module

import pytest
from helpers import FakeTransport, Verdict, attempt, machine_claim, seed_problem

from algo_coach import cli
from algo_coach.claims import standing_claims
from algo_coach.classifier import EFFORT, MODEL
from algo_coach.log import AttemptLog
from algo_coach.runs import ABORT_AFTER

TRANSPORT = import_module("algo_coach.cli.transport")


def run(monkeypatch, client: FakeTransport, *argv: str) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "classify", "--user", "u1", *argv])
    cli.main()


@pytest.fixture
def root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    seed_problem(data, id="two-codes", techniques=["greedy", "sorting"])
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    AttemptLog(data).append_attempt(attempt("a1", "two-codes"))
    return data


def test_the_command_claims_the_backlog(root, monkeypatch, capsys):
    run(monkeypatch, FakeTransport.answering(Verdict(["greedy"])))

    (claim,) = AttemptLog(root).claims()
    assert claim.techniques == ["greedy"]
    assert f"1 claim(s) written by {MODEL}, effort {EFFORT}" in capsys.readouterr().out


def test_a_run_that_landed_nothing_exits_nonzero(root, monkeypatch, capsys):
    """A key that does not work fails every attempt in turn — silence and a
    zero exit would read as a backlog with nothing left to claim."""
    client = FakeTransport.answering(Verdict(error=RuntimeError("bad key")))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, client)

    assert exit_info.value.code == 1
    # On stderr, where the run reported it as it happened — stdout carries the
    # counts, and a second copy of the reason would only say it twice.
    assert "bad key" in capsys.readouterr().err


def test_a_missing_key_fails_before_the_run(root, monkeypatch, capsys):
    """One error, not the same one per attempt: nothing about the backlog can
    make an unset key work."""
    client = FakeTransport.answering(Verdict(["greedy"]))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "classify", "--user", "u1"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "OPENROUTER_API_KEY" in capsys.readouterr().err
    assert client.calls == []


def test_the_command_reports_each_attempt_as_it_goes(root, monkeypatch, capsys):
    """On stderr, so the counts on stdout stay the command's output."""
    run(monkeypatch, FakeTransport.answering(Verdict(["greedy"])))

    captured = capsys.readouterr()
    assert "[1/1] two-codes" in " ".join(captured.err.split())
    assert "greedy" in captured.err
    assert "[1/1]" not in captured.out


def test_an_aborted_run_says_so_and_exits_nonzero(root, monkeypatch, capsys):
    """A run the classifier was unreachable for is not a backlog with nothing
    left to claim, and the reason is printed once rather than per attempt."""
    for index in range(ABORT_AFTER + 1):
        AttemptLog(root).append_attempt(attempt(f"extra{index}", "two-codes"))
    client = FakeTransport.answering(*[Verdict(error=RuntimeError("bad key"))] * ABORT_AFTER)

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, client)

    assert exit_info.value.code == 1
    assert "aborted" in capsys.readouterr().err


def test_redo_re_derives_a_stale_machine_claim(root, monkeypatch, capsys):
    log = AttemptLog(root)
    log.append_claim(machine_claim("a1", ["sorting"], model=MODEL, prompt_hash="ffffffffffff"))

    run(monkeypatch, FakeTransport.answering(Verdict(["greedy"])), "--redo")

    standing = standing_claims(AttemptLog(root).claims())["a1"]
    assert standing.techniques == ["greedy"]
    assert (standing.model, standing.effort) == (MODEL, EFFORT)
    assert "1 stale machine claim(s) re-derived" in capsys.readouterr().out


def test_the_limit_caps_the_run(root, monkeypatch, capsys):
    AttemptLog(root).append_attempt(attempt("a2", "two-codes"))
    client = FakeTransport.answering(Verdict(["greedy"]))

    run(monkeypatch, client, "--limit", "1")

    assert len(client.calls) == 1
    assert len(AttemptLog(root).claims()) == 1
