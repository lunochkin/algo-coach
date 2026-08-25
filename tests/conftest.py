import pytest

from algo_coach.cli.transport import CREDENTIALS
from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem


@pytest.fixture(autouse=True)
def off_the_developer_machine(tmp_path, monkeypatch):
    """Nothing outside the repo decides a test's outcome.

    `main` loads `.env` from the working directory and reads the environment
    for defaults, so a developer's own key or user id would otherwise reach
    every command a test runs.
    """
    monkeypatch.chdir(tmp_path)
    for name in ("ALGO_COACH_USER", *CREDENTIALS):
        monkeypatch.delenv(name, raising=False)


def seed_problem(store: ProblemStore, *, id: str) -> None:
    store.put(
        Problem(
            id=id,
            title="Two Sum",
            statement="Given an array, return ...",
        )
    )


@pytest.fixture
def problems(tmp_path) -> ProblemStore:
    """Two stored problems. An attempt names a minted `problem_id`, so what a
    test needs from here is something to point at."""
    store = ProblemStore(tmp_path)
    seed_problem(store, id="minted-u1")
    seed_problem(store, id="minted-u2")
    return store


@pytest.fixture
def data_root(tmp_path) -> ProblemStore:
    """The same seeding, under the directory the CLI treats as DATA_ROOT."""
    store = ProblemStore(tmp_path / "data")
    seed_problem(store, id="minted-u1")
    seed_problem(store, id="minted-local")
    return store
