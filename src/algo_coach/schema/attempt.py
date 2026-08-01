from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


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


class AttemptOrigin(StrEnum):
    PUSH = "push"  # arrived through the push API
    ENGINE = "engine"  # produced by the engine's own drill loop


class Attempt(BaseModel):
    """One real practice attempt. Append-only: never rewritten, never deleted,
    and schema changes stay additive."""

    id: str  # engine-minted; never accepted from a client
    # (external_id, user_id) — idempotency key for pushed attempts
    external_id: str | None = None
    user_id: str
    problem_id: str
    # A platform records when a submission landed, rarely when work started.
    # Optional so a backfill of past attempts counts instead of being rejected.
    started_at: datetime | None = None
    finished_at: datetime
    language: str = "python"
    time_to_solve_sec: float | None = None
    solved: bool
    origin: AttemptOrigin
    # The origin platform's own status, verbatim and unmapped; `solved` is the
    # projection over it. Kept raw so a later mapping can re-read it.
    source_status: str | None = None
    self_label: FailureMode | None = None
    notes: str | None = None
    code: str | None = None
    tests: list[TestResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def _pushed_attempts_declare_their_origin(self) -> Attempt:
        """A client cannot claim the engine produced what it pushed."""
        if self.external_id is not None and self.origin is not AttemptOrigin.PUSH:
            raise ValueError("an attempt carrying an external_id originates from the push API")
        return self


class ClaimSource(StrEnum):
    USER = "user"
    CLASSIFIER = "classifier"


class TechniqueClaim(BaseModel):
    """Which techniques an attempt used — what per-technique progress is
    measured from. Append-only: a later claim never rewrites an earlier one,
    latest wins on read.

    One record names every technique of one attempt, asserted together, so a
    revision replaces the whole set. Per-technique records would leave a later
    claim merging with an earlier one, with nothing to say which stands.
    """

    id: str  # engine-minted
    created_at: datetime
    attempt_id: str
    techniques: list[str] = Field(min_length=1)
    source: ClaimSource  # required: a mislabelled claim cannot be corrected later
    model: str | None = None
    prompt_version: str | None = None

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TechniqueClaim:
        """A machine claim is re-derivable, so it must say by what; versions on
        a user claim would name a model that never touched it."""
        versioned = self.model is not None and self.prompt_version is not None
        if self.source is ClaimSource.CLASSIFIER and not versioned:
            raise ValueError("a classifier claim needs model and prompt_version")
        if self.source is ClaimSource.USER and (self.model or self.prompt_version):
            raise ValueError("a user claim carries no model or prompt_version")
        return self
