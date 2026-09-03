import os
from importlib import import_module

import pytest
from helpers import FakeTransport, Verdict

from algo_coach import cli

TRANSPORT = import_module("algo_coach.cli.transport")


@pytest.fixture
def cwd(tmp_path, monkeypatch):
    """The working directory every test already runs in, empty of a `.env`
    until one of these writes it."""
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    answering = FakeTransport.answering(Verdict(["greedy"]))
    monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: answering)
    monkeypatch.setattr("sys.argv", ["algo-coach", "classify", "--user", "u1"])
    return tmp_path


def test_a_key_in_the_file_is_loaded(cwd):
    (cwd / ".env").write_text("OPENROUTER_API_KEY=from-file\n")

    cli.main()  # the credential check would exit 2 on an unset key


def test_the_environment_wins_over_the_file(cwd, monkeypatch):
    """The shell is the deliberate one: a key exported for a single run is not
    overwritten by the file it was exported to override."""
    (cwd / ".env").write_text("OPENROUTER_API_KEY=from-file\n")
    monkeypatch.setenv("OPENROUTER_API_KEY", "from-shell")

    cli.main()

    assert os.environ["OPENROUTER_API_KEY"] == "from-shell"


def test_no_file_is_not_an_error(cwd):
    """Nothing to load is the normal case once the key is exported."""
    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2


def test_ctrl_c_ends_the_command_rather_than_reporting_it(monkeypatch, capsys):
    """Every command appends as it goes, so a stopped run keeps what landed.
    The traceback would name the line the prompt was waiting on, which is
    where the user was rather than what went wrong."""
    monkeypatch.setattr(cli, "board", _interrupted)
    monkeypatch.setattr("sys.argv", ["algo-coach", "board"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == cli.INTERRUPTED
    assert "interrupted" in capsys.readouterr().err


def _interrupted(*_args, **_kwargs):
    raise KeyboardInterrupt
