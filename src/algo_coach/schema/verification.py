"""One execution of a solution against a problem's cases.

Its own record, because the outcome is a fact about the run rather than about
the code. A `TIMEOUT` is decided by the cap and the machine, and a `CRASHED`
can come from the runner rather than the solution. The same solution run twice
can differ, so a result stored on the solution would claim a permanence it does
not have.

Re-running is therefore legal and expected, as re-deriving a reading is. What
distinguishes two runs of one solution is their configuration, which is why the
cap is stored beside the results.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from algo_coach.schema.case import CaseOutcome, CaseResult


class Verification(BaseModel):
    """What one run decided, case by case."""

    id: str  # engine-minted, as every reference in the log is
    created_at: datetime
    # the canonical that was run. Phase 8 runs an attempt on the same path,
    # and what that reference looks like is settled there
    canonical_id: str = Field(min_length=1)
    # the wall-clock cap per case, which is what decided any `TIMEOUT`. Stored
    # because two runs under different caps are not comparable, and the
    # outcome is the only thing that would show it
    timeout_ms: int = Field(gt=0)
    # one entry per case the solution was run against
    results: list[CaseResult] = Field(default_factory=list)

    @property
    def outcome(self) -> CaseOutcome | None:
        """How the run went as a whole, folded from the cases.

        The same four words a case uses. A timeout is a fact about the run
        that surfaces at one case, so the level it is read at does not change
        what it means.

        The most severe failure stands. A solution that only ran slowly is
        otherwise correct, and that is a different remedy from one returning a
        wrong answer.

        `None` where no case was run. An empty set would otherwise fold to
        passed and claim a verification that never happened.
        """
        if not self.results:
            return None
        for outcome in (CaseOutcome.CRASHED, CaseOutcome.WRONG, CaseOutcome.TIMEOUT):
            if any(one.outcome is outcome for one in self.results):
                return outcome
        return CaseOutcome.PASSED

    @property
    def verified(self) -> bool:
        """Exemplary and verified are different properties, and this is the
        second. Derived, as every aggregate is."""
        return self.outcome is CaseOutcome.PASSED
