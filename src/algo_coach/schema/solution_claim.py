"""Which techniques a solution used, as one writer says."""

from datetime import datetime

from pydantic import Field, model_validator

from algo_coach.schema.attempt import ClaimSource
from algo_coach.schema.provenance import MachineProvenance


class SolutionClaim(MachineProvenance):
    id: str
    created_at: datetime
    solution_id: str = Field(min_length=1)
    # Empty is a stored verdict; no `declined`, since a solution claim is
    # deliberate.
    techniques: list[str] = Field(default_factory=list[str])
    source: ClaimSource  # required: a mislabelled claim cannot be corrected later
    informed_by: list[str] = Field(
        default_factory=list[str]
    )  # calls its author saw, not provenance

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> SolutionClaim:
        """Rejects provenance that disagrees with the source."""
        self.check_provenance(self.source is ClaimSource.CLASSIFIER)
        return self
