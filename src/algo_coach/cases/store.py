from pathlib import Path

from algo_coach.schema import TestCase
from algo_coach.storage import JsonlLog


class CaseLog(JsonlLog[TestCase]):
    """The cases that decide a problem."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "test_cases.jsonl", TestCase)

    def cases(self) -> list[TestCase]:
        return self.all()

    def for_problem(self, problem_id: str) -> list[TestCase]:
        return [one for one in self.all() if one.problem_id == problem_id]
