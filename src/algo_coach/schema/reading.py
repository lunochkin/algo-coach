"""Which techniques a solution used, as one reader read it."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class ReadingSource(StrEnum):
    USER = "user"
    CLASSIFIER = "classifier"


class TechniqueReading(MachineProvenance):
    id: str
    created_at: datetime
    solution_id: str = Field(min_length=1)
    # Empty is a stored verdict; no `declined`, since a reading is deliberate.
    techniques: list[str] = Field(default_factory=list)
    source: ReadingSource  # required: a mislabelled reading cannot be corrected later
    informed_by: list[str] = Field(default_factory=list)  # calls its author saw, not provenance

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TechniqueReading:
        """Rejects provenance that disagrees with the source."""
        self.check_provenance(self.source is ReadingSource.CLASSIFIER)
        return self
