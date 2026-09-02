from pathlib import Path

from algo_coach.schema import Problem


class ProblemStore:
    """One file per problem, named by its engine-minted id; a write replaces it."""

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

    def all(self) -> list[Problem]:
        if not self.problems_path.exists():
            return []
        return [
            Problem.model_validate_json(path.read_text())
            for path in sorted(self.problems_path.glob("*.json"))
        ]
