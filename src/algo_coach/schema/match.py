from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class MatchSource(StrEnum):
    USER = "user"  # a hand annotation: the set a machine run is scored against
    GENERATOR = "generator"  # what it was told to write; an assertion, so no provenance
    CLASSIFIER = "classifier"


class TemplateMatch(MachineProvenance):
    """Whether one solution displays one of a card's templates. One record per
    pair — `content.md` gives why not a set."""

    id: str
    created_at: datetime
    template_id: str  # minted at card import, as `solution_id` is when the problem lands
    solution_id: str
    matched: bool  # a negative is stored, or every re-run re-tests every non-match
    source: MatchSource
    informed_by: list[str] = Field(default_factory=list)  # calls its author saw, not provenance

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TemplateMatch:
        self.check_provenance(self.source is MatchSource.CLASSIFIER)
        return self
