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


class Attempt(BaseModel):
    """One real practice attempt. Append-only: never rewritten, never deleted,
    and schema changes stay additive."""

    id: str  # engine-minted, as every reference in the log is
    user_id: str
    problem_id: str
    # An attempt nobody timed stays untimed rather than carrying a duration
    # reconstructed after the fact.
    started_at: datetime | None = None
    finished_at: datetime
    language: str | None = None  # not always recorded; a default would guess
    time_to_solve_sec: float | None = None
    solved: bool
    code: str | None = None


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
    """Which techniques an attempt used. Per-technique progress is measured
    from this. Append-only: a later claim never rewrites an earlier one, and
    the latest wins on read.

    One record names every technique of one attempt, asserted together, so a
    revision replaces the whole set. Per-technique records would leave a later
    claim merging with an earlier one, with nothing to say which stands.

    A claim may name none of them. That is its author saying the candidates do
    not cover what the code did. From the classifier it is a reading worth
    keeping, since an unstored one is re-read by every later run, and the
    answer never changes while the question does not.

    A user says so with `declined`, never with an empty list alone. The loop
    records nothing where they skip, so emptiness on its own would be
    indistinguishable from a stated decline, and a skipped answer would read
    as an answer given. The flag is what tells the two apart.
    """

    # Empty is a verdict, not an absent one: the classifier read the code and
    # found the candidates did not cover it. Stored so the reading is not paid
    # for on every later run, and the resolver leaves the fallback standing
    # rather than treating an empty set as an answer.
    techniques: list[str] = Field(default_factory=list)
    # The user's decline, stated rather than inferred from an empty list. Only
    # they need it: the classifier answers or fails, and a failure writes no
    # claim, so its empty set was never ambiguous. Making it required of both
    # would tighten a field every stored machine decline already carries
    # loosely, which the schema rule does not allow.
    declined: bool = False
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
        if self.source is ClaimSource.USER and not (self.techniques or self.declined):
            # The drill loop records nothing where the user skips, so an empty
            # user claim is a lost answer rather than a stated one — unless it
            # says which it is.
            raise ValueError("a user claim names at least one technique, or declines")
        if self.techniques and self.declined:
            # One record would assert that the candidates do not apply and name
            # two of them. Nothing reading it could say which was meant.
            raise ValueError("a claim that names techniques cannot decline")

        self.check_provenance(self.source is ClaimSource.CLASSIFIER)
        return self
