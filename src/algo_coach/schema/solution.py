from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class SolutionRole(StrEnum):
    """Stored rather than inferred: both pass the same cases."""

    CANONICAL = "canonical"
    REFERENCE = "reference"


class Solution(MachineProvenance):
    id: str
    created_at: datetime
    problem_id: str = Field(min_length=1)
    role: SolutionRole
    code: str = Field(min_length=1)  # what a template match reads beside the statement

    @model_validator(mode="after")
    def _provenance_required(self) -> Solution:
        """A model wrote every solution, so there is no hand arm to exempt."""
        self.check_provenance(True)
        return self
