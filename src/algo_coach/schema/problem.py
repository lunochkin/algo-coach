from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance
from algo_coach.schema.target import one_target


class ProblemDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ProblemStatus(StrEnum):
    CREATED = "created"  # written and verified; served, since no gate over the corpus exists yet
    RETIRED = "retired"  # no longer served; `retired_reason` says why


class RetirementReason(StrEnum):
    DEFECTIVE = "defective"  # its cases decide something else; its attempts leave mastery


class Problem(MachineProvenance):
    id: str
    title: str
    techniques: list[str] = Field(
        default_factory=list[str]
    )  # read off the canonicals; re-derivable
    difficulty: ProblemDifficulty | None = None
    statement: str = Field(min_length=1)  # what the problem asks; matching reads it
    # The target: what the generator was told, never a claim that the problem
    # exercises nothing else. One of the two, by the kind the target named.
    # The template arm makes the first template match provenance
    target_template_id: str | None = Field(default=None, min_length=1)
    target_technique: str | None = Field(default=None, min_length=1)
    status: ProblemStatus = ProblemStatus.CREATED
    # A field rather than a record of its own, unlike a self-label or a claim:
    # nothing but a by-hand pass ever retires a problem.
    retired_reason: RetirementReason | None = None

    @property
    def served(self) -> bool:
        # every status but retirement, since no gate stands between landing and
        # serving until Phase 14. The serving call, the candidates and the gap
        # report read this one rule
        return self.status is not ProblemStatus.RETIRED

    @model_validator(mode="after")
    def _provenance_required(self) -> Problem:
        self.check_provenance(True)
        return self

    @model_validator(mode="after")
    def _one_target(self) -> Problem:
        one_target(self.target_template_id, self.target_technique)
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
