from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class ProblemDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Problem(MachineProvenance):
    id: str  # engine-minted, as every reference in the log is
    title: str
    # derived from the problem's canonical solutions, so re-derivable at any
    # time: a canonical added later can widen them
    techniques: list[str] = Field(default_factory=list)
    difficulty: ProblemDifficulty | None = None
    # what the problem asks; matching reads it, and a problem without one can
    # never be matched
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def _provenance_required(self) -> Problem:
        self.check_provenance(True)
        return self
