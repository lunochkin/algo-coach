"""Alembic's entry: the shared metadata, with every store's tables on it, and
the database DATABASE_URL names."""

import importlib
import os
from pathlib import Path

from alembic import context
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine

import algo_coach
from algo_coach.storage import metadata

# every `table.py` under the package, so a store's new table reaches the
# migration without a list here to update
source = Path(algo_coach.__file__).parent
for path in sorted(source.rglob("table.py")):
    parts = path.relative_to(source).with_suffix("").parts
    importlib.import_module(".".join(("algo_coach", *parts)))


def url() -> str:
    # a caller migrating a database of its own names it, as the test fixture
    # does; otherwise an exported variable wins over the file, as the CLI reads
    load_dotenv(find_dotenv(usecwd=True))
    found = context.config.attributes.get("url") or os.environ.get("DATABASE_URL")
    if not found:
        raise SystemExit("DATABASE_URL names the database to migrate")
    # psycopg 3, whatever scheme the URL was written with
    return found.replace("postgres://", "postgresql+psycopg://", 1).replace(
        "postgresql://", "postgresql+psycopg://", 1
    )


def offline() -> None:
    context.configure(url=url(), target_metadata=metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def online() -> None:
    engine = create_engine(url())
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        # closed here rather than by the garbage collector, which a caller in
        # the same process, as the test fixture is, would see as a leak
        engine.dispose()


if context.is_offline_mode():
    offline()
else:
    online()
