"""`.env` at the working directory, loaded before anything reads the
environment. The key never reaches the store or a command line."""

import os
from importlib import import_module

import pytest
from helpers import FakeClient, Verdict

from algo_coach import cli

CLIENT = import_module("algo_coach.cli.client")


@pytest.fixture
def cwd(tmp_path, monkeypatch):
    """The working directory every test already runs in, empty of a `.env`
    until one of these writes it."""
    monkeypatch.setattr(cli, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(CLIENT, "Anthropic", lambda: FakeClient.answering(Verdict(["greedy"])))
    monkeypatch.setattr("sys.argv", ["algo-coach", "classify", "--user", "u1"])
    return tmp_path


def test_a_key_in_the_file_is_loaded(cwd):
    (cwd / ".env").write_text("ANTHROPIC_API_KEY=from-file\n")

    cli.main()  # the credential check would exit 2 on an unset key


def test_the_environment_wins_over_the_file(cwd, monkeypatch):
    """The shell is the deliberate one: a key exported for a single run is not
    overwritten by the file it was exported to override."""
    (cwd / ".env").write_text("ANTHROPIC_API_KEY=from-file\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "from-shell")

    cli.main()

    assert os.environ["ANTHROPIC_API_KEY"] == "from-shell"


def test_no_file_is_not_an_error(cwd):
    """Nothing to load is the normal case once the key is exported."""
    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
