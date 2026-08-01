from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class FailureMode(StrEnum):
    SPEED = "speed"  # solved, but too slowly
    RUST = "rust"  # once-fluent technique, retrieval/fluency failure
    GAP = "gap"  # technique not actually known
    SYNTAX = "syntax"  # language/implementation slip
    NONE = "none"  # clean pass


class TestResult(BaseModel):
    name: str
    passed: bool
    runtime_ms: float | None = None


class Attempt(BaseModel):
    """One real practice attempt. Records are append-only: never rewritten,
    never deleted; schema changes must be additive."""

    id: str  # engine-minted; never accepted from a client
    # (external_id, user_id) — idempotency key for pushed attempts
    external_id: str | None = None
    user_id: str
    problem_id: str
    started_at: datetime
    finished_at: datetime
    language: str = "python"
    time_to_solve_sec: float
    solved: bool
    session: str | None = None
    self_label: FailureMode | None = None
    notes: str | None = None
    code: str
    tests: list[TestResult] = Field(default_factory=list)


class AttemptTechnique(BaseModel):
    """The user's claim about which technique an attempt used. Append-only:
    a later claim never rewrites an earlier one, latest wins on read."""

    id: str  # engine-minted
    created_at: datetime
    attempt_id: str
    technique: str
