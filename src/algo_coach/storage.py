"""The two shapes every store takes: an append-only log of JSON lines, and a
directory of one file per record. The schema is the contract, and this is what
swaps underneath it."""

from pathlib import Path

from pydantic import BaseModel


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
        return [
            self.model.model_validate_json(line)
            for line in self.path.read_text().splitlines()
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
        (self.path / f"{record.id}.json").write_text(record.model_dump_json(indent=2) + "\n")

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


__all__ = ["FileStore", "JsonlLog"]
