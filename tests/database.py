"""One Postgres database per xdist worker, migrated to head once and emptied
after every test that uses it.

The server is named by TEST_DATABASE_URL, from the environment or the repo's
`.env`, and needs the right to create databases and to set
`session_replication_role`, which a superuser has. A test taking the fixture is
marked `integration`, and a run without a server deselects those. The databases
the fixture creates are its own, `algo_coach_test_<worker>`, and never the one
DATABASE_URL names.
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from dotenv import dotenv_values
from helpers import CALL_ROW
from sqlalchemy import Engine, create_engine, insert, make_url, text

from algo_coach.storage import UTC, Database, metadata

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
        # DELETE, where TRUNCATE takes a lock and new files per table and costs
        # a tenth of a second under a dozen workers. The replica role skips the
        # triggers refusing a delete, and the foreign keys the order would
        # otherwise have to follow
        conn.execute(text("SET LOCAL session_replication_role = replica"))
        names = conn.execute(
            text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                " AND tablename <> 'alembic_version'"
            )
        ).scalars()
        for name in names:
            conn.execute(text(f'DELETE FROM "{name}"'))
        conn.execute(
            text(
                "SELECT setval(format('%I.%I', schemaname, sequencename), 1, false)"
                " FROM pg_sequences WHERE schemaname = 'public'"
            )
        )


@pytest.fixture(scope="session")
def database_engine(worker_id: str) -> Iterator[Engine]:
    server = server_url()
    if server is None:
        # failed rather than skipped: a run without a server selects the unit
        # tests alone, `-m "not integration"`, and says so
        pytest.fail("TEST_DATABASE_URL names no Postgres server; run -m 'not integration'")
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

    engine = create_engine(url, **UTC)
    yield engine
    engine.dispose()
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    admin.dispose()


@pytest.fixture
def database(database_engine: Engine) -> Iterator[Database]:
    """The handle a test builds its stores from: the worker's database, empty
    when the test starts but for the helper call, and emptied after."""
    handle = Database(engine=database_engine)
    shared(handle)
    yield handle
    emptied(database_engine)


def shared(database: Database) -> None:
    """The call `PROVENANCE` cites, which every machine record the shared
    helpers build names. A test counting calls reads past it with `own`."""
    with database.engine.begin() as conn:
        conn.execute(insert(metadata.tables["calls"]).values(CALL_ROW))
