from pathlib import Path

from algo_coach.schema import Draft
from algo_coach.storage import FileStore


class DraftStore(FileStore[Draft]):
    """Working state rather than a log: a draft is revised as each step
    answers, and removed once the problem it became has landed."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "drafts", Draft)

    def remove(self, draft_id: str) -> None:
        # what clearing at landing does. Missing is not an error: a run that
        # died between landing and clearing leaves the next one this to do
        (self.path / f"{draft_id}.json").unlink(missing_ok=True)
