from pathlib import Path

from algo_coach.schema import Problem


class ProblemStore:
    """Store for problems. One file per problem, named by its engine-minted id.

    Unlike the attempt log, this is a mutable cache: a re-pushed problem
    overwrites the descriptive fields it carries. Identity never moves.
    """

    def __init__(self, root: Path):
        self.problems_path = root / "problems"

    def put(self, problem: Problem) -> None:
        self.problems_path.mkdir(parents=True, exist_ok=True)
        path = self.problems_path / f"{problem.id}.json"
        path.write_text(problem.model_dump_json(indent=2) + "\n")

    def get(self, problem_id: str) -> Problem | None:
        path = self.problems_path / f"{problem_id}.json"
        if not path.exists():
            return None
        return Problem.model_validate_json(path.read_text())

    def by_external(self, user_id: str, external_id: str) -> Problem | None:
        """Identity across pushes: the same pair is the same problem."""
        for problem in self.all():
            if problem.user_id == user_id and problem.external_id == external_id:
                return problem
        return None

    def all(self) -> list[Problem]:
        if not self.problems_path.exists():
            return []
        return [
            Problem.model_validate_json(path.read_text())
            for path in sorted(self.problems_path.glob("*.json"))
        ]
