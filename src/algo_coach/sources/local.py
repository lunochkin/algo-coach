import json
from pathlib import Path

from algo_coach.schema.attempt import TestResult
from algo_coach.sources.protocol import Problem, TestCase


class LocalSource:
    """File-based ProblemSource: one JSON file per problem under root
    (fields of Problem + optional "test_cases"). Reference implementation
    and the open on-ramp for the protocol; verify() lands with the
    execute-verify slice."""

    name = "local"

    def __init__(self, root: Path):
        self.root = root

    def get_problem(self, problem_id: str) -> Problem:
        return Problem.model_validate(self._load(problem_id))

    def get_test_cases(self, problem_id: str) -> list[TestCase]:
        raw = self._load(problem_id).get("test_cases", [])
        return [TestCase.model_validate(tc) for tc in raw]

    def verify(self, problem_id: str, code: str) -> list[TestResult]:
        raise NotImplementedError("execute-verify slice")

    def _load(self, problem_id: str) -> dict:
        return json.loads((self.root / f"{problem_id}.json").read_text())
