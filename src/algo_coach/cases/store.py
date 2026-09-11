from algo_coach.cases.table import test_cases
from algo_coach.schema import TestCase
from algo_coach.storage import Database, Log


class CaseLog(Log[TestCase]):
    """The cases that decide a problem."""

    def __init__(self, root: Database) -> None:
        super().__init__(root, test_cases, TestCase)

    def cases(self) -> list[TestCase]:
        return self.all()

    def for_problem(self, problem_id: str) -> list[TestCase]:
        return self.where(test_cases.c.problem_id == problem_id)
