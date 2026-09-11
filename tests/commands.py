"""Running one CLI command in a test, as a shell would."""

from algo_coach import cli
from algo_coach.cli import transport as TRANSPORT
from algo_coach.storage import Database, directory


def run_cli(monkeypatch, *argv: str, client=None) -> None:
    """`algo-coach <argv>` through `main`. With `client`, the transport is the
    fake and a key is set, since a command checks for one before it asks."""
    if client is not None:
        monkeypatch.setenv("OPENROUTER_API_KEY", "test")
        monkeypatch.setattr(TRANSPORT, "OpenRouter", lambda _api, **_: client)
    monkeypatch.setattr("sys.argv", ["algo-coach", *argv])
    cli.main()


def data_root(database, monkeypatch):
    """Points the command under test at the test's own stores: its directory as
    `DATA_ROOT`, its database as the one DATABASE_URL names. Returns the handle
    the test seeds those stores through."""
    monkeypatch.setattr(cli, "DATA_ROOT", directory(database))
    if isinstance(database, Database):
        url = database.engine.url.render_as_string(hide_password=False)
        monkeypatch.setenv("DATABASE_URL", url)
    return database
