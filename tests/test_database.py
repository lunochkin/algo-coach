from database import emptied
from sqlalchemy import func, insert, select, text

from algo_coach.calls.table import calls
from algo_coach.storage import metadata


def call_row(id: str) -> dict:
    return {
        "id": id,
        "created_at": "2026-09-11T08:00:00Z",
        "model": "a-model",
        "effort": "medium",
        "prompt": "a prompt",
        "prompt_hash": "0123456789ab",
        "response": "{}",
    }


def test_the_worker_s_database_is_built_by_the_migrations(database):
    """The tables a test writes to are the ones a deployment runs, rather than
    ones the metadata creates on its own."""
    with database.connect() as conn:
        head = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        tables = set(
            conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            ).scalars()
        )

    assert head
    assert tables >= set(metadata.tables)


def test_a_test_starts_on_an_empty_database(database):
    with database.connect() as conn:
        assert conn.execute(select(func.count()).select_from(calls)).scalar_one() == 0


def test_emptying_removes_every_row_and_restarts_the_append_order(database):
    """A later test reads no row this one wrote, and numbers its first row as
    this one did."""
    with database.begin() as conn:
        conn.execute(insert(calls), [call_row("c1"), call_row("c2")])

    emptied(database)

    with database.begin() as conn:
        assert conn.execute(select(func.count()).select_from(calls)).scalar_one() == 0
        conn.execute(insert(calls), [call_row("c3")])
        assert conn.execute(select(calls.c.appended)).scalar_one() == 1
