from pathlib import Path

from algo_coach.schema import TemplateMatch
from algo_coach.storage import JsonlLog


class MatchLog(JsonlLog[TemplateMatch]):
    """Template matches, one line per pair and reading."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "template_matches.jsonl", TemplateMatch)

    def matches(self) -> list[TemplateMatch]:
        return self.all()
