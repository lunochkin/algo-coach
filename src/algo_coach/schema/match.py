from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class MatchSource(StrEnum):
    USER = "user"  # a hand annotation: the labelled set a machine run is scored against
    # what the generator was told to write. An assertion rather than a
    # reading, so it carries no provenance: nothing re-derives it, and the
    # solution it points at already names the call that wrote it
    GENERATOR = "generator"
    CLASSIFIER = "classifier"


class TemplateMatch(MachineProvenance):
    """Whether one solution displays one of a card's templates.

    A form is displayed by code, so the subject is a solution rather than a
    problem. A problem reaches a template through its canonicals, which is a
    fold rather than a record.

    The engine's own work, never an author's. A card names no solution, so what
    a rung covers is read off the corpus rather than written down beside it.

    One record per pair, not a set per template. Solutions arrive one at a
    time, and a set record would rewrite pairs that were already settled
    whenever the corpus grew. The pairs are independent, and a new solution
    adds to them. A claim asserts a whole set because the set is the assertion.
    A match asserts one pair.

    Append-only, like every other reading. A re-run at a new configuration
    appends its verdict, and what the old one said stays readable.
    """

    id: str  # engine-minted, as every reference in the log is
    created_at: datetime
    # Both minted: the template at card import, the solution when its problem
    # lands. So a match cannot be authored — neither reference exists in a seed
    # file.
    template_id: str
    solution_id: str
    # The verdict, and a negative is stored: without it every re-run re-tests
    # every non-match forever, which on a growing corpus is nearly all the work.
    matched: bool
    source: MatchSource
    # The calls whose verdicts were in view when the pair was annotated, empty
    # for a blind one. Not provenance: provenance is what produced a reading,
    # this is what its author had seen. A hand record carries this and never
    # that. Named one by one, because an annotation made after seeing one
    # matcher's verdict is still independent of another's, and configurations
    # are scored against the same records.
    informed_by: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TemplateMatch:
        self.check_provenance(self.source is MatchSource.CLASSIFIER)
        return self
