"""One execution of code against a problem's cases: a solution's, or an
attempt's. `corpus.md` fixes what a stored result means."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from algo_coach.schema.case import CaseOutcome, CaseResult, severest
from algo_coach.schema.record import AttemptRecord


class Execution(BaseModel):
    model_config = ConfigDict(frozen=True)

    cap_ms: int = Field(gt=0)  # the per-case cap that decided any `TIMEOUT`
    runner: str = Field(min_length=1)  # backend and interpreter, opaque; never parsed
    results: list[CaseResult] = Field(default_factory=list[CaseResult])  # one entry per case run

    @property
    def outcome(self) -> CaseOutcome | None:
        return severest(one.outcome for one in self.results)

    @property
    def verified(self) -> bool:
        return self.outcome is CaseOutcome.PASSED


class Verification(Execution):
    id: str
    created_at: datetime
    solution_id: str = Field(min_length=1)  # in either role


class AttemptVerification(AttemptRecord, Execution):
    """Private to the user, where a solution's run is product data: `log.md`."""
