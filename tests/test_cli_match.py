from importlib import import_module

import pytest
from matching import FakeTransport, Verdict, card, problem, seeded, stored

from algo_coach import cli
from algo_coach.matches import EFFORT, MODEL, MatchLog

TRANSPORT = import_module("algo_coach.cli.transport")


def run(monkeypatch, client: FakeTransport, *argv: str) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test")
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", "match", *argv])
    cli.main()


@pytest.fixture
def root(tmp_path, monkeypatch):
    data = tmp_path / "data"
    seeded(data, card())
    stored(data, problem("p1", techniques=["sliding-window"]))
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    return data


def test_the_command_matches_the_corpus(root, monkeypatch, capsys):
    run(monkeypatch, FakeTransport.answering(Verdict(["fixed-window"])))

    records = MatchLog(root).matches()
    assert sorted(match.matched for match in records) == [False, True]
    out = capsys.readouterr().out
    assert f"1 card/problem question(s) read by {MODEL}, effort {EFFORT}" in out
    assert "1 match(es), 1 non-match(es) recorded" in out


def test_an_unseeded_card_is_named_before_the_run(root, monkeypatch, capsys):
    """A slug nothing was imported under would otherwise run over an empty
    corpus and report a clean zero."""
    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, FakeTransport.answering(), "--card", "monotonic-stack")

    assert exit_info.value.code == 2
    assert "no card 'monotonic-stack'" in capsys.readouterr().err


def test_a_run_that_landed_nothing_exits_nonzero(root, monkeypatch, capsys):
    client = FakeTransport.answering(Verdict(error=RuntimeError("bad key")))

    with pytest.raises(SystemExit) as exit_info:
        run(monkeypatch, client)

    assert exit_info.value.code == 1
    assert "bad key" in capsys.readouterr().err


def test_a_missing_key_fails_before_the_run(root, monkeypatch, capsys):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: FakeTransport.answering())
    monkeypatch.setattr("sys.argv", ["algo-coach", "match"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "OPENROUTER_API_KEY unset" in capsys.readouterr().err
