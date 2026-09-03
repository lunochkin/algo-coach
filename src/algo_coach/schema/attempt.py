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
    id: str
    user_id: str
    problem_id: str
    started_at: datetime | None = None  # absent where nothing timed the sitting
    finished_at: datetime
    language: str | None = None  # not always recorded; a default would guess
    time_to_solve_sec: float | None = None
    solved: bool
    code: str | None = None


class SelfLabel(AttemptRecord):
    """The user's own verdict on why an attempt went the way it did."""

    mode: FailureMode


class ClaimSource(StrEnum):
    USER = "user"
    CLASSIFIER = "classifier"


class Confidence(StrEnum):
    GUESS = "guess"
    LEANING = "leaning"
    SURE = "sure"


class TechniqueClaim(AttemptRecord, MachineProvenance):
    """Which techniques an attempt used, as one writer claimed them."""

    techniques: list[str] = Field(default_factory=list)  # empty is a verdict, and is stored
    declined: bool = False  # the user's, stated rather than inferred from an empty set
    source: ClaimSource  # required: a mislabelled claim cannot be corrected later
    informed_by: list[str] = Field(default_factory=list)  # calls its author saw, not provenance
    confidence: Confidence | None = None  # absent on claims written before it was asked for

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TechniqueClaim:
        """Rejects a user claim that says nothing, a decline that names
        techniques, and provenance that disagrees with the source."""
        if self.source is ClaimSource.USER and not (self.techniques or self.declined):
            raise ValueError("a user claim names at least one technique, or declines")
        if self.techniques and self.declined:
            raise ValueError("a claim that names techniques cannot decline")

        self.check_provenance(self.source is ClaimSource.CLASSIFIER)
        return self
