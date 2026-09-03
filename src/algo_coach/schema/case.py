"""What decides whether a solution to a generated problem is correct."""

from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class ExpectedSource(StrEnum):
    """Which solution computed a case's expected output. Not `SolutionRole`
    under another name: it answers how strong the case is."""

    REFERENCE = "reference"
    CANONICAL = "canonical"


class TestCase(MachineProvenance):
    """One case of a generated problem's set. The provenance names the call
    that proposed the arguments, which is not the problem's own wherever a
    mutation round or the speedup search won the case."""

    id: str
    problem_id: str = Field(min_length=1)
    args: list[Any] = Field(default_factory=list)  # positional; empty is legal
    expected: Any  # required: `None` is a value a solution may return, so absence cannot stand in
    expected_from: ExpectedSource  # required; `mint.case` carries the rule

    @model_validator(mode="after")
    def _provenance_required(self) -> TestCase:
        """A model proposed every case's arguments, so there is no hand arm."""
        self.check_provenance(True)
        return self


class CaseOutcome(StrEnum):
    PASSED = "passed"
    WRONG = "wrong"  # returned something other than the expected value
    TIMEOUT = "timeout"  # exceeded the wall-clock cap
    CRASHED = "crashed"  # raised rather than returning


class CaseResult(BaseModel):
    case_id: str = Field(min_length=1)
    outcome: CaseOutcome
    elapsed_ms: int | None = Field(default=None, ge=0)  # absent where the child measured nothing

    @model_validator(mode="after")
    def _a_case_that_yielded_a_value_was_timed(self) -> CaseResult:
        """Rejects a `PASSED` or `WRONG` case that carries no measurement."""
        if self.outcome in (CaseOutcome.PASSED, CaseOutcome.WRONG) and self.elapsed_ms is None:
            raise ValueError(f"a {self.outcome} case carries the elapsed_ms the child measured")
        return self


def severest(outcomes: Iterable[CaseOutcome]) -> CaseOutcome | None:
    """How a set of cases went as a whole. `None` where no case was run."""
    seen = list(outcomes)
    if not seen:
        return None
    for outcome in (CaseOutcome.CRASHED, CaseOutcome.WRONG, CaseOutcome.TIMEOUT):
        if outcome in seen:
            return outcome
    return CaseOutcome.PASSED
