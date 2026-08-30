from pathlib import Path

from algo_coach.schema import Solution, SolutionRole


class SolutionLog:
    """Append-only JSONL store for the solutions a problem carries.

    Several per problem is the ordinary case, and the set is the assertion:
    two approaches to one problem are what let a rung cover a studied template
    and an optional one at once. So a second solution appends beside the first
    rather than replacing it, which a one-file-per-problem store could not
    express.
    """

    def __init__(self, root: Path):
        self.root = root
        self.solutions_path = root / "solutions.jsonl"

    def append(self, solution: Solution) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.solutions_path.open("a") as f:
            f.write(solution.model_dump_json() + "\n")

    def solutions(self) -> list[Solution]:
        """In append order: a tie on `created_at` is broken by what landed last."""
        if not self.solutions_path.exists():
            return []
        return [
            Solution.model_validate_json(line)
            for line in self.solutions_path.read_text().splitlines()
            if line.strip()
        ]

    def for_problem(self, problem_id: str, role: SolutionRole | None = None) -> list[Solution]:
        """What a problem's techniques are derived from, and what a matcher
        reads beside the statement.

        Both of those read canonicals alone: a reference is the naive approach
        the form replaces, so counting it would credit the problem with a
        technique nothing about it teaches.
        """
        return [
            one
            for one in self.solutions()
            if one.problem_id == problem_id and (role is None or one.role is role)
        ]
