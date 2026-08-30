"""A solution the engine wrote for a problem, in one of two roles.

Not an attempt: no user and no sitting. The canonical displays the template's
form and is what a rung teaches, so exemplary and verified are different
properties and the record needs both. The reference is written from the
statement alone, and is what computes the expected outputs and what a timing
bar measures against.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class SolutionRole(StrEnum):
    """Which of the two a solution is.

    Stored rather than inferred: both are verified against the same cases, so
    passing says nothing about the role, and a reader taking a reference for a
    canonical would teach the approach the card exists to replace.
    """

    CANONICAL = "canonical"
    REFERENCE = "reference"


class Solution(MachineProvenance):
    """The code and what produced it, and nothing about how it ran.

    Immutable once written. Whether it passes is a fact about a run, and a
    `Verification` holds that.
    """

    id: str  # engine-minted, as every reference in the log is
    created_at: datetime
    problem_id: str = Field(min_length=1)
    role: SolutionRole
    # what a template match reads beside the statement. Which form a problem
    # exercises is a question about the solution, and a statement only implies
    # one
    code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _provenance_required(self) -> Solution:
        """A model wrote every solution, so there is no hand arm to exempt as
        there is for a match."""
        self.check_provenance(True)
        return self
