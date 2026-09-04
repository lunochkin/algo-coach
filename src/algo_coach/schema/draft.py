from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.outcome import Discard


class WritingState(StrEnum):
    """How far a problem has been written. One state per step that can fail, in
    the order `flows.md` gives; `landed` is where `ProblemStatus` starts."""

    DRAFTED = "drafted"
    CHECKED = "checked"
    REFERENCED = "referenced"
    AGREED = "agreed"
    BUILT = "built"
    SEARCHED = "searched"
    HARDENED = "hardened"
    LANDED = "landed"
    REJECTED = "rejected"  # terminal; `gate` says what reached it


class Draft(BaseModel):
    """One attempt at writing a problem, held as it is written. Working state
    rather than a log: it is revised in place and cleared at landing."""

    id: str = Field(min_length=1)  # the writing id the site outcomes group under
    state: WritingState = WritingState.DRAFTED
    # what rejected the answer, as the same gate on the site whose output made
    # it decidable. A field rather than a record: nothing but the run writes it
    gate: Discard | None = None

    @model_validator(mode="after")
    def _rejection_names_its_gate(self) -> Draft:
        """Rejects a rejected draft with no gate, and a gate on one a resume
        could still carry forward."""
        rejected = self.state is WritingState.REJECTED
        if rejected and self.gate is None:
            raise ValueError("a rejected draft names the gate that reached it")
        if not rejected and self.gate is not None:
            raise ValueError(f"a {self.state} draft carries no gate")
        return self
