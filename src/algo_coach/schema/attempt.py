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


class VerdictSource(StrEnum):
    CLIENT = "client"  # the pushing client says so
    ENGINE = "engine"  # the engine ran the tests itself


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
    verdict_source: VerdictSource  # what `solved` and `tests` rest on
    session: str | None = None
    self_label: FailureMode | None = None
    notes: str | None = None
    code: str
    tests: list[TestResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def _pushed_verdicts_are_claims(self) -> Attempt:
        """A pushed attempt was solved outside the engine, which owns no test
        cases for its problem — so the platform cannot have verified it."""
        if self.external_id is not None and self.verdict_source is not VerdictSource.CLIENT:
            raise ValueError("a pushed attempt's verdict can only come from the client")
        return self


class ClaimSource(StrEnum):
    USER = "user"
    CLASSIFIER = "classifier"


class AttemptTechnique(BaseModel):
    """A claim about which technique an attempt used, and what per-technique
    progress is measured from. Append-only: a later claim never rewrites an
    earlier one, latest wins on read."""

    id: str  # engine-minted
    created_at: datetime
    attempt_id: str
    technique: str
    source: ClaimSource  # required: a mislabelled claim cannot be corrected later
    model: str | None = None
    prompt_version: str | None = None

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> AttemptTechnique:
        """Machine claims are re-derivable, so they must say by what. User
        claims are not, so version fields on one would name nothing."""
        versioned = self.model is not None and self.prompt_version is not None
        if self.source is ClaimSource.CLASSIFIER and not versioned:
            raise ValueError("a classifier claim needs model and prompt_version")
        if self.source is ClaimSource.USER and (self.model or self.prompt_version):
            raise ValueError("a user claim carries no model or prompt_version")
        return self
