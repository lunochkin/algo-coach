from pathlib import Path

from algo_coach.schema import SiteOutcome
from algo_coach.storage import JsonlLog


class OutcomeLog(JsonlLog[SiteOutcome]):
    """What each call site left. A re-run of one site over one item is a second
    record, as a second verification is."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "site_outcomes.jsonl", SiteOutcome)

    def outcomes(self) -> list[SiteOutcome]:
        return self.all()

    def for_writing(self, writing_id: str) -> list[SiteOutcome]:
        return [one for one in self.all() if one.writing_id == writing_id]
