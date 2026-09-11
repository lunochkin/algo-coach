"""Running one CLI command in a test, as a shell would."""

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


def connected(database, monkeypatch):
    """Points the command under test at the test's database, the one
    DATABASE_URL names, and returns the handle the test seeds it through."""
    url = database.engine.url.render_as_string(hide_password=False)
    monkeypatch.setenv("DATABASE_URL", url)
    return database
