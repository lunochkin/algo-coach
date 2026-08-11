from pathlib import Path

from algo_coach.schema import Call


class CallLog:
    """Append-only JSONL store for what was asked of a model and what returned.

    Its own file rather than a column on the claims: the claims file is parsed
    by every command that renders a board, and a prompt and a reasoning summary
    per line would make that a megabyte-scale read for information no board
    needs. Nothing on the run path reads this back — the domain decides what to
    ask from its own records — so it stays cheap to write and is loaded only by
    whoever sits down to analyse a run.
    """

    def __init__(self, root: Path):
        self.root = root
        self.path = root / "calls.jsonl"

    def append(self, call: Call) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as f:
            f.write(call.model_dump_json() + "\n")

    def all(self) -> list[Call]:
        """In append order. No index by hash: a lookup would have to say which
        of several calls on one prompt it meant, and nothing asks yet."""
        if not self.path.exists():
            return []
        return [
            Call.model_validate_json(line)
            for line in self.path.read_text().splitlines()
            if line.strip()
        ]
