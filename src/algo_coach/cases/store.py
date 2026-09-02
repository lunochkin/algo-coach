from pathlib import Path

from algo_coach.schema import TestCase


class CaseLog:
    """Append-only JSONL store for the cases that decide a problem."""

    def __init__(self, root: Path):
        self.root = root
        self.cases_path = root / "test_cases.jsonl"

    def append(self, case: TestCase) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.cases_path.open("a") as f:
            f.write(case.model_dump_json() + "\n")

    def cases(self) -> list[TestCase]:
        if not self.cases_path.exists():
            return []
        return [
            TestCase.model_validate_json(line)
            for line in self.cases_path.read_text().splitlines()
            if line.strip()
        ]

    def for_problem(self, problem_id: str) -> list[TestCase]:
        return [one for one in self.cases() if one.problem_id == problem_id]
