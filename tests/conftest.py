import pytest

from algo_coach.cli.transport import CREDENTIALS

# what signing in reads, so a developer's own clients or dev login user reach no
# route and no command
SIGN_IN = (
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "ALGO_COACH_ORIGIN",
    "ALGO_COACH_SECRET",
    "ALGO_COACH_DEV_LOGIN",
)

# the Postgres fixtures, one database per worker
pytest_plugins = ["database"]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    # a test is an integration test exactly when it takes a database, so the
    # mark follows the fixture rather than a list someone keeps
    for item in items:
        if {"database", "database_engine"} & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def off_the_developer_machine(tmp_path, monkeypatch):
    """Nothing outside the repo decides a test's outcome.

    `main` loads `.env` from the working directory and reads the environment
    for defaults, so a developer's own key or user id would otherwise reach
    every command a test runs.
    """
    monkeypatch.chdir(tmp_path)
    for name in ("DATABASE_URL", *CREDENTIALS, *SIGN_IN):
        monkeypatch.delenv(name, raising=False)
