"""One execution of a solution against a problem's cases."""

from datetime import datetime

from pydantic import BaseModel, Field

from algo_coach.schema.case import CaseOutcome, CaseResult, severest


class Verification(BaseModel):
    id: str
    created_at: datetime
    solution_id: str = Field(min_length=1)  # in either role
    timeout_ms: int = Field(gt=0)  # the per-case cap that decided any `TIMEOUT`
    runner: str = Field(min_length=1)  # backend and interpreter, opaque; never parsed
    results: list[CaseResult] = Field(default_factory=list)  # one entry per case run

    @property
    def outcome(self) -> CaseOutcome | None:
        return severest(one.outcome for one in self.results)

    @property
    def verified(self) -> bool:
        return self.outcome is CaseOutcome.PASSED
