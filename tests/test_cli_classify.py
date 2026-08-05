from importlib import import_module

import pytest
from helpers import FakeClient, Verdict, attempt, seed_problem

from algo_coach import cli
from algo_coach.claims import MODEL, PROMPT_VERSION
from algo_coach.claims.run import ABORT_AFTER
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.mint import classifier_claim

CLIENT = import_module("algo_coach.cli.client")


def run(monkeypatch, client: FakeClient, *argv: str) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setattr(CLIENT, "Anthropic", lambda: client)
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


def test_a_missing_key_fails_before_the_run(root, monkeypatch, capsys):
    """One error, not the same one per attempt: nothing about the backlog can
    make an unset key work."""
    client = FakeClient.answering(Verdict(["greedy"]))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setattr(CLIENT, "Anthropic", lambda: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "classify", "--user", "u1"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
    assert client.messages.calls == []


def test_an_aborted_run_says_so_and_exits_nonzero(root, monkeypatch, capsys):
    """A run the classifier was unreachable for is not a backlog with nothing
    left to claim, and the reason is printed once rather than per attempt."""
    for index in range(ABORT_AFTER + 1):
        AttemptLog(root).append_attempt(attempt(f"extra{index}", "two-tags"))
    client = FakeClient.answering(*[Verdict(error=RuntimeError("bad key"))] * ABORT_AFTER)

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, client)

    assert exit_info.value.code == 1
    assert "aborted" in capsys.readouterr().err


def test_redo_re_derives_a_stale_machine_claim(root, monkeypatch, capsys):
    log = AttemptLog(root)
    log.append_claim(classifier_claim("a1", ["sorting"], model=MODEL, prompt_version="0"))

    run(monkeypatch, FakeClient.answering(Verdict(["greedy"])), "--redo")

    standing = latest_by_attempt(AttemptLog(root).claims())["a1"]
    assert (standing.techniques, standing.prompt_version) == (["greedy"], PROMPT_VERSION)
    assert "1 stale machine claim(s) re-derived" in capsys.readouterr().out


def test_the_limit_caps_the_run(root, monkeypatch, capsys):
    AttemptLog(root).append_attempt(attempt("a2", "two-tags"))
    client = FakeClient.answering(Verdict(["greedy"]))

    run(monkeypatch, client, "--limit", "1")

    assert len(client.messages.calls) == 1
    assert len(AttemptLog(root).claims()) == 1
