"""An exemplary solution to a problem, written to display the approach.

Not an attempt: no user and no sitting. Exemplary and verified are different
properties, and the record needs both — a user's solved attempt is verified and
idiosyncratic, a generated solution is exemplary and asserted. Only one that
passes the problem's cases is both.
"""

from datetime import datetime

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class CanonicalSolution(MachineProvenance):
    """The code and what produced it, and nothing about how it ran.

    Immutable once written. Whether it passes is a fact about a run, and a
    `Verification` holds that.
    """

    id: str  # engine-minted, as every reference in the log is
    created_at: datetime
    problem_id: str = Field(min_length=1)
    # what a template match reads beside the statement. Which form a problem
    # exercises is a question about the solution, and a statement only implies
    # one
    code: str = Field(min_length=1)

    @model_validator(mode="after")
    def _provenance_required(self) -> CanonicalSolution:
        """A model wrote every canonical, so there is no hand arm to exempt as
        there is for a match."""
        self.check_provenance(True)
        return self
