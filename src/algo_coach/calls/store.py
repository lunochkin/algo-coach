from pathlib import Path

from algo_coach.schema import Call


class CallLog:
    """Append-only JSONL store for what was asked of a model and what returned."""

    def __init__(self, root: Path):
        self.root = root
        self.path = root / "calls.jsonl"

    def append(self, call: Call) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(call.model_dump_json() + "\n")

    def all(self) -> list[Call]:
        """In append order. No index by hash: several calls can share one prompt."""
        if not self.path.exists():
            return []
        return [
            Call.model_validate_json(line)
            for line in self.path.read_text().splitlines()
            if line.strip()
        ]
