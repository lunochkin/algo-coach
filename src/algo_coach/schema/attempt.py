from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.provenance import MachineProvenance
from algo_coach.schema.record import AttemptRecord


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
    language: str | None = None  # not always recorded; a default would guess
    time_to_solve_sec: float | None = None
    solved: bool
    origin: AttemptOrigin
    # The origin platform's own status, verbatim and unmapped; `solved` is the
    # projection over it. Kept raw so a later mapping can re-read it.
    source_status: str | None = None
    notes: str | None = None
    code: str | None = None
    tests: list[TestResult] = Field(default_factory=list)

    @model_validator(mode="after")
    def _pushed_attempts_declare_their_origin(self) -> Attempt:
        """A client cannot claim the engine produced what it pushed."""
        if self.external_id is not None and self.origin is not AttemptOrigin.PUSH:
            raise ValueError("an attempt carrying an external_id originates from the push API")
        return self


class SelfLabel(AttemptRecord):
    """The user's own verdict on why an attempt went the way it did.

    A judgement made after the fact and open to revision, so it is its own
    record rather than a field on the attempt — the same reason
    `TechniqueClaim` is. Append-only, latest wins on read.

    Only ever the user's: a machine answering the same question produces a
    `Diagnosis`, which carries what model and prompt reached it. The two never
    supersede each other — the eval scores one against the other.
    """

    mode: FailureMode


class ClaimSource(StrEnum):
    USER = "user"
    CLASSIFIER = "classifier"


class Confidence(StrEnum):
    GUESS = "guess"
    LEANING = "leaning"
    SURE = "sure"


class TechniqueClaim(AttemptRecord, MachineProvenance):
    """Which techniques an attempt used — what per-technique progress is
    measured from. Append-only: a later claim never rewrites an earlier one,
    latest wins on read.

    One record names every technique of one attempt, asserted together, so a
    revision replaces the whole set. Per-technique records would leave a later
    claim merging with an earlier one, with nothing to say which stands.

    A machine claim may name none of them. That is the classifier saying the
    candidates do not cover what the code did — a reading worth keeping, since
    an unstored one is re-read by every later run and the answer never changes
    while the question does not. A user's claim may not: the loop records
    nothing where they skip, so an empty one would be a lost answer wearing the
    shape of a stated one.
    """

    # Empty is a verdict, not an absent one: the classifier read the code and
    # found the candidates did not cover it. Stored so the reading is not paid
    # for on every later run, and the resolver leaves the fallback standing
    # rather than treating an empty set as an answer.
    techniques: list[str] = Field(default_factory=list)
    source: ClaimSource  # required: a mislabelled claim cannot be corrected later
    # The calls whose readings were in view when the claim was made, empty for
    # a blind one. Not provenance: provenance is what produced a claim, this is
    # what its author had seen, so a user claim carries this and never that.
    # Named one by one rather than flagged, because a claim made after seeing
    # one configuration's reading is still independent of another's, and
    # configurations are scored against the same claims.
    informed_by: list[str] = Field(default_factory=list)
    # How sure its author was, a level rather than a float: a judgement made in
    # seconds carries no more. Absent on every claim written before it was
    # asked for, and a level nobody gave is not the same as a low one.
    confidence: Confidence | None = None
    # What produced a machine claim is `MachineProvenance`'s, whole: model,
    # how hard it was asked to think, the digest of the text sent, the build it
    # was pinned to, how it was sampled, and the call carrying the rest.

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TechniqueClaim:
        """A machine claim is re-derivable, so it must say by what; provenance
        on a user claim would name a model that never touched it."""
        if self.source is ClaimSource.USER and not self.techniques:
            # The drill loop records nothing where the user skips, so an empty
            # user claim is a lost answer rather than a stated one.
            raise ValueError("a user claim names at least one technique")

        self.check_provenance(self.source is ClaimSource.CLASSIFIER)
        return self
