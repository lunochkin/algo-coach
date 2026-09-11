"""One Postgres database per xdist worker, migrated to head once and emptied
after every test that uses it.

The server is named by TEST_DATABASE_URL, from the environment or the repo's
`.env`, and needs the right to create databases. The databases the fixture
creates are its own, `algo_coach_test_<worker>`, and never the one
DATABASE_URL names.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from sqlalchemy import Engine, create_engine, make_url, text

ROOT = Path(__file__).resolve().parent.parent


def server_url() -> str | None:
    # read before a test moves the working directory, and never from a `.env`
    # outside the repo
    found = os.environ.get("TEST_DATABASE_URL") or dotenv_values(ROOT / ".env").get(
        "TEST_DATABASE_URL"
    )
    return found.replace("postgres://", "postgresql+psycopg://", 1) if found else None


def emptied(engine: Engine) -> None:
    """Every table the migrations created, and the append order restarted, so
    no test reads a row or a number another test left."""
    with engine.begin() as conn:
        names = conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                " AND tablename <> 'alembic_version'"
            )
        ).scalars()
        listed = ", ".join(f'"{name}"' for name in names)
        if listed:
            conn.execute(text(f"TRUNCATE {listed} RESTART IDENTITY CASCADE"))


@pytest.fixture(scope="session")
def database_engine(worker_id: str) -> Iterator[Engine]:
    server = server_url()
    if server is None:
        pytest.skip("TEST_DATABASE_URL names no Postgres server to test against")
    name = f"algo_coach_test_{worker_id}"
    admin = create_engine(server, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        # a run stopped midway leaves its database behind, so each run starts
        # from nothing
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    url = make_url(server).set(database=name)

    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["url"] = url.render_as_string(hide_password=False)
    command.upgrade(config, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def database(database_engine: Engine) -> Iterator[Engine]:
    """The worker's database, empty when the test starts and emptied after."""
    yield database_engine
    emptied(database_engine)
