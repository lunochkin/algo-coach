from pathlib import Path

from algo_coach.schema import TemplateMatch


class MatchLog:
    """Append-only JSONL store for template matches, one line per pair and
    reading."""

    def __init__(self, root: Path):
        self.root = root
        self.matches_path = root / "template_matches.jsonl"

    def append(self, match: TemplateMatch) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.matches_path.open("a") as f:
            f.write(match.model_dump_json() + "\n")

    def matches(self) -> list[TemplateMatch]:
        """In append order: a tie on `created_at` is broken by what landed
        last."""
        if not self.matches_path.exists():
            return []
        return [
            TemplateMatch.model_validate_json(line)
            for line in self.matches_path.read_text().splitlines()
            if line.strip()
        ]
