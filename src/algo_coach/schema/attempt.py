from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FailureMode(str, Enum):
    SPEED = "speed"  # solved, but too slowly
    RUST = "rust"  # once-fluent technique, retrieval/fluency failure
    GAP = "gap"  # technique not actually known
    SYNTAX = "syntax"  # language/implementation slip
    NONE = "none"  # clean pass


class TestResult(BaseModel):
    name: str
    passed: bool
    runtime_ms: float | None = None


class ProblemRef(BaseModel):
    source: str  # ProblemSource id, e.g. "local"
    problem_id: str
    techniques: list[str] = Field(default_factory=list)


class Attempt(BaseModel):
    """One real practice attempt. Records are append-only: never rewritten,
    never deleted; schema changes must be additive."""

    id: str
    started_at: datetime
    finished_at: datetime
    problem: ProblemRef
    code: str
    language: str = "python"
    tests: list[TestResult] = Field(default_factory=list)
    solved: bool
    time_to_solve_sec: float
    session: str | None = None
    self_label: FailureMode | None = None
    notes: str | None = None
