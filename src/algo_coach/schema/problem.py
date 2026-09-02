from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class ProblemDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ProblemStatus(StrEnum):
    CREATED = "created"  # written and verified, not yet cleared to serve
    ACTIVE = "active"  # served by the drill loop
    RETIRED = "retired"  # no longer served; `retired_reason` says why


class RetirementReason(StrEnum):
    DEFECTIVE = "defective"  # its cases decide something else; its attempts leave mastery
    TELEGRAPHED = "telegraphed"  # it names its own approach; its attempts are kept


class Problem(MachineProvenance):
    id: str
    title: str
    techniques: list[str] = Field(default_factory=list)  # read off the canonicals; re-derivable
    difficulty: ProblemDifficulty | None = None
    statement: str = Field(min_length=1)  # what the problem asks; matching reads it
    # The template the brief named, where it named one: an assertion rather
    # than a reading, and never a claim that the problem exercises nothing
    # else. Absent on a problem written from a technique brief.
    generated_for: str | None = Field(default=None, min_length=1)
    status: ProblemStatus = ProblemStatus.CREATED
    # A field rather than a record of its own, unlike a self-label or a claim:
    # nothing but the user ever retires a problem.
    retired_reason: RetirementReason | None = None

    @model_validator(mode="after")
    def _provenance_required(self) -> Problem:
        self.check_provenance(True)
        return self

    @model_validator(mode="after")
    def _retirement_names_its_reason(self) -> Problem:
        """Rejects a retired problem with no reason, and a reason on one that
        is still served."""
        retired = self.status is ProblemStatus.RETIRED
        if retired and self.retired_reason is None:
            raise ValueError("a retired problem names its retired_reason")
        if not retired and self.retired_reason is not None:
            raise ValueError(f"a {self.status} problem carries no retired_reason")
        return self
