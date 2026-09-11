"""The two shapes every store takes: an append-only log of JSON lines, and a
directory of one file per record. The schema is the contract, and this is what
swaps underneath it. The Postgres tables the stores move to are declared against
the conventions below, as `docs/architecture/README.md` gives them."""

from enum import StrEnum
from functools import cache, cached_property
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy import (
    BigInteger,
    Column,
    Connection,
    DateTime,
    Engine,
    Enum,
    ForeignKey,
    Identity,
    MetaData,
    Text,
    create_engine,
    select,
)


class Database:
    """What every store is built from: the Postgres database, and the directory
    a store not yet moved onto Postgres still writes its files under."""

    def __init__(self, directory: Path, *, url: str | None = None, engine: Engine | None = None):
        self.directory = directory
        self._url = url
        self._engine = engine

    @cached_property
    def engine(self) -> Engine:
        # made on first use, so a command no store on Postgres runs needs no
        # database
        if self._engine is not None:
            return self._engine
        if not self._url:
            raise RuntimeError("DATABASE_URL names no database")
        return create_engine(self._url.replace("postgres://", "postgresql+psycopg://", 1))

    def close(self) -> None:
        # only an engine this handle made: one handed in belongs to its maker
        if self._engine is None and "engine" in self.__dict__:
            self.engine.dispose()


def directory(root: Database | Path) -> Path:
    # a store still on files takes a handle or, as its tests do, the directory
    return root.directory if isinstance(root, Database) else root


class JsonlLog[T: BaseModel]:
    """Append-only: one record per line, read back in append order, so a tie on
    `created_at` is broken by what landed last."""

    def __init__(self, root: Database | Path, filename: str, model: type[T]) -> None:
        # the handle as given, so a caller builds a sibling store from it
        self.root = root
        self.path = directory(root) / filename
        self.model = model

    def append(self, record: T) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(record.model_dump_json() + "\n")

    def all(self) -> list[T]:
        if not self.path.exists():
            return []
        # split on the newline alone: `splitlines` also splits on U+2028 and
        # its kin, which JSON leaves unescaped inside a string
        return [
            self.model.model_validate_json(line)
            for line in self.path.read_text().split("\n")
            if line.strip()
        ]


class FileStore[T: BaseModel]:
    """One file per record, named by its engine-minted id; a write replaces it.
    For what is revised in place, where a log is for what is not."""

    def __init__(self, root: Database | Path, dirname: str, model: type[T]) -> None:
        self.root = root
        self.path = directory(root) / dirname
        self.model = model

    def put(self, record: T) -> None:
        self.path.mkdir(parents=True, exist_ok=True)
        # the bound is the model, and the id is this store's own contract
        key = getattr(record, "id")  # noqa: B009
        (self.path / f"{key}.json").write_text(record.model_dump_json(indent=2) + "\n")

    def get(self, id: str) -> T | None:
        path = self.path / f"{id}.json"
        if not path.exists():
            return None
        return self.model.model_validate_json(path.read_text())

    def all(self) -> list[T]:
        if not self.path.exists():
            return []
        return [
            self.model.model_validate_json(path.read_text())
            for path in sorted(self.path.glob("*.json"))
        ]


# named, so a migration Alembic generates names each constraint the same on
# every database it runs against
metadata = MetaData(
    naming_convention={
        "pk": "%(table_name)s_pkey",
        "fk": "%(table_name)s_%(column_0_name)s_fkey",
        "uq": "%(table_name)s_%(column_0_N_name)s_key",
        "ix": "%(table_name)s_%(column_0_N_name)s_idx",
        "ck": "%(table_name)s_%(constraint_name)s_check",
    }
)


# one type per enum, however many tables use it: two declarations of one
# Postgres type would have a migration create it twice
@cache
def enumerated(kind: type[StrEnum]) -> Enum:
    # by value, the string a stored JSON record already carries, rather than by
    # member name
    return Enum(
        kind,
        name=_snake(kind.__name__),
        values_callable=_values,
    )


def timestamp() -> DateTime:
    return DateTime(timezone=True)


def appended_column() -> Column[int]:
    # the order an append-only record landed in, which a JSON line kept for
    # free: a reader breaks a tie on `created_at` by it. `ALWAYS`, so no writer
    # supplies an order of its own
    return Column("appended", BigInteger, Identity(always=True), nullable=False, unique=True)


def call_column(*, nullable: bool) -> Column[Any]:
    # the call holds the configuration: `machine.md`
    return Column("call_id", Text, ForeignKey("calls.id"), nullable=nullable)


# what a machine record reads from its call, rather than storing a copy:
# `machine.md`
CONFIGURATION = ("model", "effort", "prompt_hash", "pin", "provider", "temperature", "cost")


def configurations(conn: Connection, call_ids: set[str]) -> dict[str, dict[str, Any]]:
    """Each named call's configuration, as the records it wrote carry it."""
    calls = metadata.tables["calls"]
    rows = conn.execute(
        select(calls.c.id, *(calls.c[name] for name in CONFIGURATION)).where(
            calls.c.id.in_(call_ids)
        )
    ).mappings()
    return {row["id"]: {name: row[name] for name in CONFIGURATION} for row in rows}


def configured(row: dict[str, Any], known: dict[str, dict[str, Any]]) -> dict[str, Any]:
    # none where the row names no call, as a user's record carries none
    return row | known.get(row.get("call_id") or "", dict.fromkeys(CONFIGURATION))


def called(conn: Connection, records: list[BaseModel]) -> None:
    """Refuses a record copying a configuration its call does not carry: the
    table keeps the call alone, and the difference would be lost on write."""
    known = configurations(conn, {one.model_dump()["call_id"] for one in records} - {None})
    for record in records:
        dumped = record.model_dump()
        if dumped["call_id"] is None:
            continue
        call = known.get(dumped["call_id"])
        if call is None:
            raise ValueError(
                f"{type(record).__name__} names call {dumped['call_id']}, which is not stored"
            )
        differ = [name for name in CONFIGURATION if dumped[name] != call[name]]
        if differ:
            raise ValueError(
                f"{type(record).__name__} copies {', '.join(differ)} "
                f"its call {dumped['call_id']} does not carry"
            )


def _values(kind: type[StrEnum]) -> list[str]:
    return [member.value for member in kind]


def _snake(name: str) -> str:
    return "".join(f"_{char.lower()}" if char.isupper() else char for char in name).lstrip("_")


__all__ = [
    "CONFIGURATION",
    "Database",
    "FileStore",
    "JsonlLog",
    "appended_column",
    "call_column",
    "called",
    "configurations",
    "configured",
    "directory",
    "enumerated",
    "metadata",
    "timestamp",
]
