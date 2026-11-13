"""A later judgement of a problem's difficulty, as `corpus.md` gives."""

from datetime import datetime

from pydantic import Field, model_validator

from algo_coach.schema.attempt import ClaimSource
from algo_coach.schema.problem import ProblemDifficulty
from algo_coach.schema.provenance import MachineProvenance


class DifficultyRating(MachineProvenance):
    id: str
    created_at: datetime
    problem_id: str = Field(min_length=1)
    difficulty: ProblemDifficulty
    source: ClaimSource

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> DifficultyRating:
        self.check_provenance(self.source is ClaimSource.CLASSIFIER)
        return self
