import pytest

from algo_coach.cli.client import CREDENTIALS
from algo_coach.problems import ProblemStore
from algo_coach.schema import Problem, ProblemOwner


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


def seed_problem(store: ProblemStore, *, id: str, external_id: str, user_id: str) -> None:
    store.put(
        Problem(
            id=id,
            external_id=external_id,
            user_id=user_id,
            owner=ProblemOwner.USER,
            title="Two Sum",
            title_slug="two-sum",
        )
    )


@pytest.fixture
def problems(tmp_path) -> ProblemStore:
    """A store holding problem "p1" for both "u1" and "u2".

    Attempt ingest resolves `problem_external_id` through this, so an attempt
    is only pushable once its problem has been pushed — and each user resolves
    to their own copy.
    """
    store = ProblemStore(tmp_path)
    seed_problem(store, id="minted-u1", external_id="p1", user_id="u1")
    seed_problem(store, id="minted-u2", external_id="p1", user_id="u2")
    return store


@pytest.fixture
def data_root(tmp_path) -> ProblemStore:
    """The same seeding, under the directory the CLI treats as DATA_ROOT."""
    store = ProblemStore(tmp_path / "data")
    seed_problem(store, id="minted-u1", external_id="p1", user_id="u1")
    seed_problem(store, id="minted-local", external_id="p1", user_id="local")
    return store
