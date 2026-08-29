from pathlib import Path

from algo_coach.schema import CanonicalSolution


class CanonicalLog:
    """Append-only JSONL store for canonical solutions.

    Several per problem is the ordinary case, and the set is the assertion:
    two approaches to one problem are what let a rung cover a studied template
    and an optional one at once. So a second canonical appends beside the
    first rather than replacing it, which a one-file-per-problem store could
    not express.
    """

    def __init__(self, root: Path):
        self.root = root
        self.canonicals_path = root / "canonical_solutions.jsonl"

    def append(self, canonical: CanonicalSolution) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.canonicals_path.open("a") as f:
            f.write(canonical.model_dump_json() + "\n")

    def canonicals(self) -> list[CanonicalSolution]:
        """In append order: a tie on `created_at` is broken by what landed last."""
        if not self.canonicals_path.exists():
            return []
        return [
            CanonicalSolution.model_validate_json(line)
            for line in self.canonicals_path.read_text().splitlines()
            if line.strip()
        ]

    def for_problem(self, problem_id: str) -> list[CanonicalSolution]:
        """What a problem's techniques are derived from, and what a matcher
        reads beside the statement."""
        return [one for one in self.canonicals() if one.problem_id == problem_id]
