from pathlib import Path

from algo_coach.schema import TestCase


class CaseLog:
    """Append-only JSONL store for the cases that decide a problem.

    A case is never revised. One found wrong is discarded with the problem it
    belonged to, since the cases define the problem and the statement is what
    can disagree with them. What does happen is addition: an edge case, or one
    sized to force a timeout, lands beside the set written with the statement.
    """

    def __init__(self, root: Path):
        self.root = root
        self.cases_path = root / "test_cases.jsonl"

    def append(self, case: TestCase) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.cases_path.open("a") as f:
            f.write(case.model_dump_json() + "\n")

    def cases(self) -> list[TestCase]:
        """In append order, which is the order a run decides them in."""
        if not self.cases_path.exists():
            return []
        return [
            TestCase.model_validate_json(line)
            for line in self.cases_path.read_text().splitlines()
            if line.strip()
        ]

    def for_problem(self, problem_id: str) -> list[TestCase]:
        """The set a run covers whole. Every problem carries the cases that
        decide it, so this is what the engine judges a submission against."""
        return [one for one in self.cases() if one.problem_id == problem_id]
