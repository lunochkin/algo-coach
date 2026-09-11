"""One Postgres database per xdist worker, kept between runs while the
migrations stay the same, and emptied after every test that uses it.

The server is named by TEST_DATABASE_URL, from the environment or the repo's
`.env`, and needs the right to create databases and to set
`session_replication_role`, which a superuser has. A test taking the fixture is
marked `integration`, and a run without a server deselects those. The databases
the fixture creates are its own, `algo_coach_test_<worker>`, and never the one
DATABASE_URL names.
"""

import hashlib
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
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


def migrated() -> str:
    """A digest of every migration, stamped on a worker's database: a database
    stamped with another digest was migrated by other files."""
    digest = hashlib.sha256()
    for path in sorted((ROOT / "migrations" / "versions").glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


@pytest.fixture(scope="session")
def database_engine(worker_id: str) -> Iterator[Engine]:
    server = server_url()
    if server is None:
        # failed rather than skipped: a run without a server selects the unit
        # tests alone, `-m "not integration"`, and says so
        pytest.fail("TEST_DATABASE_URL names no Postgres server; run -m 'not integration'")
    name = f"algo_coach_test_{worker_id}"
    url = make_url(server).set(database=name)
    stamp = migrated()
    admin = create_engine(server, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        stamped = conn.execute(
            text(
                "SELECT shobj_description(oid, 'pg_database') FROM pg_database"
                " WHERE datname = :name"
            ),
            {"name": name},
        ).scalar()
        # kept between runs, since creating and migrating a database costs a
        # second a worker. Stamped only once migrated, so a run stopped midway
        # leaves a database the next run recreates
        if stamped != stamp:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
            conn.execute(text(f'CREATE DATABASE "{name}"'))
            # imported here: a kept database needs no migration, and the import
            # costs every worker a sixth of a second
            from alembic import command  # noqa: PLC0415
            from alembic.config import Config  # noqa: PLC0415

            config = Config(str(ROOT / "alembic.ini"))
            config.attributes["url"] = url.render_as_string(hide_password=False)
            command.upgrade(config, "head")
            conn.execute(text(f"COMMENT ON DATABASE \"{name}\" IS '{stamp}'"))
    admin.dispose()

    engine = create_engine(url, **UTC)
    # a run stopped midway leaves the rows of the test it stopped in
    emptied(engine)
    yield engine
    engine.dispose()


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
