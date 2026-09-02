from pathlib import Path

from algo_coach.schema import Solution, SolutionRole


class SolutionLog:
    """Append-only JSONL store for the solutions a problem carries."""

    def __init__(self, root: Path):
        self.root = root
        self.solutions_path = root / "solutions.jsonl"

    def append(self, solution: Solution) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.solutions_path.open("a") as f:
            f.write(solution.model_dump_json() + "\n")

    def solutions(self) -> list[Solution]:
        if not self.solutions_path.exists():
            return []
        return [
            Solution.model_validate_json(line)
            for line in self.solutions_path.read_text().splitlines()
            if line.strip()
        ]

    def for_problem(self, problem_id: str, role: SolutionRole | None = None) -> list[Solution]:
        return [
            one
            for one in self.solutions()
            if one.problem_id == problem_id and (role is None or one.role is role)
        ]
