from datetime import datetime
from enum import StrEnum

from pydantic import model_validator

from algo_coach.schema.provenance import MachineProvenance


class MatchSource(StrEnum):
    USER = "user"  # a hand annotation: the labelled set a machine run is scored against
    CLASSIFIER = "classifier"


class TemplateMatch(MachineProvenance):
    """Whether one problem exercises one of a card's templates.

    The engine's own work, never an author's. A card names no problem, so what
    a rung covers is read off the corpus rather than written down beside it.

    One record per pair, not a set per template. Problems arrive a push at a
    time, and a set record would rewrite pairs that were already settled
    whenever the corpus grew. The pairs are independent, and a push only adds
    to them. A claim asserts a whole set because the set is the assertion. A
    match asserts one pair.

    Append-only, like every other reading. A re-run at a new configuration
    appends its verdict, and what the old one said stays readable.
    """

    id: str  # engine-minted; never accepted from a client
    created_at: datetime
    # Both minted: the template at card import, the problem at ingest. Which is
    # why a match cannot be authored — neither reference exists in a seed file.
    template_id: str
    problem_id: str
    # The verdict, and a negative is stored: without it every re-run re-tests
    # every non-match forever, which on a growing corpus is nearly all the work.
    matched: bool
    source: MatchSource

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TemplateMatch:
        self.check_provenance(self.source is MatchSource.CLASSIFIER)
        return self
