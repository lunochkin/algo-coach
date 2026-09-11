"""The two shapes every store takes: an append-only log of JSON lines, and a
directory of one file per record. The schema is the contract, and this is what
swaps underneath it. The Postgres tables the stores move to are declared against
the conventions below, as `docs/architecture/README.md` gives them."""

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Enum, ForeignKey, MetaData, Text


class JsonlLog[T: BaseModel]:
    """Append-only: one record per line, read back in append order, so a tie on
    `created_at` is broken by what landed last."""

    def __init__(self, root: Path, filename: str, model: type[T]) -> None:
        self.root = root
        self.path = root / filename
        self.model = model

    def append(self, record: T) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
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

    def __init__(self, root: Path, dirname: str, model: type[T]) -> None:
        self.root = root
        self.path = root / dirname
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
        "uq": "%(table_name)s_%(column_0_name)s_key",
        "ix": "%(table_name)s_%(column_0_name)s_idx",
        "ck": "%(table_name)s_%(constraint_name)s_check",
    }
)


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


def call_column(*, nullable: bool) -> Column[Any]:
    # the call holds the configuration: `machine.md`
    return Column("call_id", Text, ForeignKey("calls.id"), nullable=nullable)


def _values(kind: type[StrEnum]) -> list[str]:
    return [member.value for member in kind]


def _snake(name: str) -> str:
    return "".join(f"_{char.lower()}" if char.isupper() else char for char in name).lstrip("_")


__all__ = [
    "FileStore",
    "JsonlLog",
    "call_column",
    "enumerated",
    "metadata",
    "timestamp",
]
