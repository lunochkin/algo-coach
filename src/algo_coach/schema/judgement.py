"""A judgement item: a template's form, clean or carrying one mutant.
`content.md` gives the items, and `log.md` the exercise they serve."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from algo_coach.schema.case import CaseOutcome


class ItemStatus(StrEnum):
    SERVED = "served"
    RETIRED = "retired"  # its template's code moved; its answers keep it readable


class JudgementItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    created_at: datetime
    template_id: str
    # the template's code the item was built from; a moved digest retires it
    form_digest: str = Field(min_length=1)
    code: str = Field(min_length=1)  # as shown: no comments, no harness
    clean: bool
    line: int | None = None  # the flawed line in `code`, counted from 1
    change: str | None = None  # what the mutant changed on that line
    # the case the flawed code fails, and what it gave there
    case_args: list[Any] | None = None
    case_expected: Any = None  # `None` is a value an answer may be
    outcome: CaseOutcome | None = None  # wrong or crashed, never timed out
    returned: Any = None  # the flawed code's value, where it returned one
    status: ItemStatus = ItemStatus.SERVED

    @model_validator(mode="after")
    def _a_flaw_names_its_line_and_case(self) -> JudgementItem:
        flawed = (self.line, self.change, self.case_args, self.outcome)
        if self.clean and any(one is not None for one in flawed):
            raise ValueError("a clean item names no flaw")
        if not self.clean and any(one is None for one in flawed):
            raise ValueError("a flawed item names its line, its change and its case")
        if self.outcome is CaseOutcome.TIMEOUT:
            raise ValueError("a flaw is read off the code, and a timeout is not")
        return self


__all__ = ["ItemStatus", "JudgementItem"]
