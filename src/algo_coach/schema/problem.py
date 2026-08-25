from enum import StrEnum

from pydantic import BaseModel, Field


class ProblemDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Problem(BaseModel):
    id: str  # engine-minted, as every reference in the log is
    title: str
    title_slug: str
    # derived from the problem's canonical solutions, so re-derivable at any
    # time: a canonical added later can widen them
    techniques: list[str] = Field(default_factory=list)
    difficulty: ProblemDifficulty | None = None
    # what the problem asks; matching reads it, and a problem without one can
    # never be matched
    statement: str = Field(min_length=1)
