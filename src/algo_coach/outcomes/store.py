from pathlib import Path

from algo_coach.schema import SiteOutcome


class OutcomeLog:
    """Append-only JSONL store for what each call site left. A re-run of one
    site over one item is a second record, as a second verification is."""

    def __init__(self, root: Path):
        self.root = root
        self.outcomes_path = root / "site_outcomes.jsonl"

    def append(self, outcome: SiteOutcome) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.outcomes_path.open("a") as f:
            f.write(outcome.model_dump_json() + "\n")

    def outcomes(self) -> list[SiteOutcome]:
        if not self.outcomes_path.exists():
            return []
        return [
            SiteOutcome.model_validate_json(line)
            for line in self.outcomes_path.read_text().splitlines()
            if line.strip()
        ]

    def for_writing(self, writing_id: str) -> list[SiteOutcome]:
        return [one for one in self.outcomes() if one.writing_id == writing_id]
