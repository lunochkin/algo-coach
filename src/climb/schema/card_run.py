"""That a card was started, and the probes the start gave it.

Studying a card is an explicit act, and the ladder is measured from the start:
`content.md` gives why a problem solved before it counts toward nothing.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Probe(BaseModel):
    """One problem a run was given, testing whether the form is recognised
    unprompted. Drawn from outside the ladder, which teaches the form."""

    model_config = ConfigDict(frozen=True)

    problem_id: str = Field(min_length=1)
    assigned_at: datetime


class CardRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    user_id: str = Field(min_length=1)
    card_id: str = Field(min_length=1)
    started_at: datetime
    # later probes append, so what was offered and when stays readable
    probes: list[Probe] = Field(default_factory=list[Probe])

    @model_validator(mode="after")
    def _a_probe_is_given_no_earlier_than_the_start(self) -> CardRun:
        early = [one for one in self.probes if one.assigned_at < self.started_at]
        if early:
            raise ValueError("a probe is assigned at the start or after it")
        return self

    @model_validator(mode="after")
    def _one_probe_per_problem(self) -> CardRun:
        """Rejects a problem offered twice: the second offer tests no
        recognition the first did not."""
        offered = [one.problem_id for one in self.probes]
        if len(set(offered)) != len(offered):
            raise ValueError("a run offers a problem as a probe once")
        return self
