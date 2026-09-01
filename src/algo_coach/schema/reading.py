"""Which techniques a solution used.

A reading rather than a claim. The question is the same one a `TechniqueClaim`
answers about an attempt, and everything else differs: the subject is code the
engine wrote, the record is product data rather than the user's private
testimony, and the candidates are the whole vocabulary rather than the
problem's own techniques.

That last difference is what forbids one record for both. A problem's
techniques are folded from these readings, and those techniques are the
fallback an unclaimed attempt resolves to. One record type would make the
fallback a fold over records of the type it falls back for.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class ReadingSource(StrEnum):
    """Who read the solution.

    Its own enum rather than the claim's. A user claim is testimony about the
    attempt its author sat for, where a user reading adjudicates code nobody
    sat for — the same two words naming two different acts.
    """

    USER = "user"
    CLASSIFIER = "classifier"


class TechniqueReading(MachineProvenance):
    """Which techniques one solution used, as one reader read it.

    Append-only, as every reading is. A re-run at a new configuration appends
    its verdict, and what an earlier one said stays readable. The user's stands
    over any machine reading however late, as a claim resolves.

    One record names every technique of one solution, asserted together, so a
    later reading replaces the whole set rather than merging with it.

    There is no `declined`. A claim needs one because the drill loop records
    nothing where the user skips, which makes an empty set ambiguous. A reading
    is only ever written deliberately, so an empty one is the verdict that the
    vocabulary does not cover this code.
    """

    id: str  # engine-minted, as every reference in the log is
    created_at: datetime
    # The solution read. A form is displayed by code and so is a technique, so
    # the subject is the solution rather than the problem it answers.
    solution_id: str = Field(min_length=1)
    # Empty is a verdict rather than an absent one: this reader found that no
    # code in the vocabulary describes this solution. Stored so the reading is
    # not paid for again.
    techniques: list[str] = Field(default_factory=list)
    source: ReadingSource  # required: a mislabelled reading cannot be corrected later
    # The calls whose readings were in view when a hand record was made, empty
    # for a blind one. Not provenance: provenance is what produced a reading,
    # this is what its author had seen.
    informed_by: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _provenance_matches_source(self) -> TechniqueReading:
        """A machine reading is re-derivable, so it must say by what;
        provenance on a hand one would name a model that never touched it."""
        self.check_provenance(self.source is ReadingSource.CLASSIFIER)
        return self
