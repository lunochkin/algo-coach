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
    # an exported variable wins over the file, as the CLI reads it
    load_dotenv(find_dotenv(usecwd=True))
    found = os.environ.get("DATABASE_URL")
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
    with create_engine(url()).connect() as connection:
        context.configure(connection=connection, target_metadata=metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    offline()
else:
    online()
