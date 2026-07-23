from typing import Protocol

from pydantic import BaseModel, Field

from algo_coach.schema.attempt import TestResult


class Problem(BaseModel):
    id: str
    title: str
    statement: str
    techniques: list[str] = Field(default_factory=list)
    difficulty: str | None = None


class TestCase(BaseModel):
    input: str
    expected: str


class ProblemSource(Protocol):
    """Boundary for all problem access. Concrete sources plug in from
    outside; this repo ships only open implementations."""

    name: str

    def get_problem(self, problem_id: str) -> Problem: ...

    def get_test_cases(self, problem_id: str) -> list[TestCase]: ...

    def verify(self, problem_id: str, code: str) -> list[TestResult]: ...
