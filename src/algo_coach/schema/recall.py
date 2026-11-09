"""One template reproduced from memory, and how it went.

Keyed to a card and a template rather than to an attempt: a recall answers no
problem and submits no solution, which `log.md` gives as why it is its own
record.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.verification import Execution


class Hint(StrEnum):
    """What the trainer gives when memory fails, in the order it gives them.
    Each answers more of the question than the last."""

    NOTES = "notes"
    FORM = "form"


# the order a hint is offered in, which the record is checked against
LADDER = (Hint.NOTES, Hint.FORM)


class RecallAttempt(Execution):
    """A form typed into a blank file and run against the template's cases."""

    id: str
    created_at: datetime
    user_id: str = Field(min_length=1)
    card_id: str = Field(min_length=1)
    template_id: str = Field(min_length=1)
    code: str  # what the user typed; empty where they ran a blank file
    # taken before the run, in the order offered. A pass with hints is a pass
    # with hints, and the field is what says so
    hints: list[Hint] = Field(default_factory=list[Hint])

    # the recall the trainer measures: reproduced with no hint taken
    @property
    def cold(self) -> bool:
        return self.verified and not self.hints

    @model_validator(mode="after")
    def _the_hints_are_a_prefix_of_the_ladder(self) -> RecallAttempt:
        """Rejects a hint taken out of order, and one taken twice. The trainer
        names the next hint, so a later one is reached through the earlier."""
        if tuple(self.hints) != LADDER[: len(self.hints)]:
            raise ValueError(f"the hints are taken in order: {', '.join(LADDER)}")
        return self
