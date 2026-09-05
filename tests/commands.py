"""Running one CLI command in a test, as a shell would."""

from pathlib import Path

from algo_coach import cli
from algo_coach.cli import transport as TRANSPORT


def run_cli(monkeypatch, *argv: str, client=None) -> None:
    """`algo-coach <argv>` through `main`. With `client`, the transport is the
    fake and a key is set, since a command checks for one before it asks."""
    if client is not None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test")
        monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", *argv])
    cli.main()


def data_root(tmp_path, monkeypatch) -> Path:
    """The directory the command under test reads as `DATA_ROOT`."""
    data = tmp_path / "data"
    monkeypatch.setattr(cli, "DATA_ROOT", data)
    return data
