"""What a client sends. The engine's own records are `Attempt` and `Problem`;
these are the payloads they are built from.

Engine-owned fields have no field here to arrive in, so a client cannot supply
identity or provenance by sending it. Unknown keys are ignored rather than
rejected, so a newer client stays pushable to an older engine.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from algo_coach.schema.attempt import FailureMode, TestResult
from algo_coach.schema.problem import ProblemDifficulty


class ProblemPush(BaseModel):
    """One problem. The engine owns `id`, `user_id`, `owner` and `techniques` —
    the last derived from `source_tags` on every push."""

    external_id: str = Field(min_length=1)  # identity across pushes, with the user
    title: str
    title_slug: str
    url: str | None = None
    platform: str | None = None
    source_tags: list[str] = Field(default_factory=list)
    difficulty: ProblemDifficulty | None = None


class AttemptPush(BaseModel):
    """One attempt. The engine owns `id`, `user_id`, `problem_id` and `origin`.

    Only `finished_at` and `solved` are required beyond identity: a platform
    records when a submission landed and how it fared, and rarely more.
    """

    external_id: str = Field(min_length=1)  # idempotency token, with the user
    problem_external_id: str = Field(min_length=1)  # resolved to the minted id
    finished_at: datetime
    solved: bool
    started_at: datetime | None = None
    language: str | None = None
    time_to_solve_sec: float | None = None
    source_status: str | None = None
    self_label: FailureMode | None = None
    notes: str | None = None
    code: str | None = None
    tests: list[TestResult] = Field(default_factory=list)
