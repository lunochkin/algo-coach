from pathlib import Path

from algo_coach.schema import Solution, SolutionRole
from algo_coach.storage import JsonlLog


class SolutionLog(JsonlLog[Solution]):
    """The solutions a problem carries, in every role."""

    def __init__(self, root: Path) -> None:
        super().__init__(root, "solutions.jsonl", Solution)

    def solutions(self) -> list[Solution]:
        return self.all()

    def for_problem(self, problem_id: str, role: SolutionRole | None = None) -> list[Solution]:
        return [
            one
            for one in self.all()
            if one.problem_id == problem_id and (role is None or one.role is role)
        ]
