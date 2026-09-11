from algo_coach.schema import Solution, SolutionRole
from algo_coach.solutions.table import solutions
from algo_coach.storage import Database, Log


class SolutionLog(Log[Solution]):
    """The solutions a problem carries, in every role."""

    def __init__(self, root: Database) -> None:
        super().__init__(root, solutions, Solution)

    def solutions(self) -> list[Solution]:
        return self.all()

    def for_problem(self, problem_id: str, role: SolutionRole | None = None) -> list[Solution]:
        if role is None:
            return self.where(solutions.c.problem_id == problem_id)
        return self.where(solutions.c.problem_id == problem_id, solutions.c.role == role)
