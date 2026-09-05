from pathlib import Path

from algo_coach.schema import Verification
from algo_coach.storage import JsonlLog


class VerificationLog(JsonlLog[Verification]):
    """Verification runs; neither of two runs of one solution supersedes the
    other."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "verifications.jsonl", Verification)

    def verifications(self) -> list[Verification]:
        return self.all()

    def for_solution(self, solution_id: str) -> list[Verification]:
        return [one for one in self.all() if one.solution_id == solution_id]
