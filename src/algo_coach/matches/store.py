from algo_coach.matches.table import template_matches
from algo_coach.schema import TemplateMatch
from algo_coach.storage import Database, Log


class MatchLog(Log[TemplateMatch]):
    """Template matches, one row per pair and writer."""

    def __init__(self, root: Database) -> None:
        super().__init__(root, template_matches, TemplateMatch)

    def matches(self) -> list[TemplateMatch]:
        return self.all()
