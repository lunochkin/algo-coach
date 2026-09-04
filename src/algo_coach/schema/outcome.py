"""What one generation call site left on one attempt at writing a problem.

A run prints its stages and the process then ends. What a configuration cost
and what the gates said about its answer is only readable from a record.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class CallSite(StrEnum):
    """The four calls writing a problem takes. `Bench` names one configuration
    per entry, and a test pins the two lists together."""

    GENERATOR = "generator"
    BLIND = "blind"
    DISCRIMINATION = "discrimination"
    INPUTS = "inputs"


class Discard(StrEnum):
    # named rather than a boolean: a run reports how its problems were lost
    NO_VALUE = "no_value"
    MISDECLARED = "misdeclared"
    UNTESTED = "untested"
    DISAGREED = "disagreed"
    # the four above say the statement, the canonical or the cases were wrong.
    # This one says none of them was: the problem does not exercise the form
    # its template claims, so no site's answer was rejected and no site outcome
    # carries it
    UNEXERCISED = "unexercised"


class SiteOutcome(MachineProvenance):
    id: str
    created_at: datetime
    site: CallSite
    # minted per attempt at one problem, so the four sites of one attempt group
    # and a discarded draft still has an identity
    writing_id: str = Field(min_length=1)
    # absent where the problem was written from a technique brief, which
    # names no form
    template_id: str | None = None
    problem_id: str | None = None  # only where the attempt landed
    # what rejected this site's answer, absent where nothing did. The gate is
    # filed under the site whose output made it decidable
    gate: Discard | None = None
    detail: str = ""
    # the mutation loop. `mutants` is what the canonical yielded, on the site
    # that wrote it
    mutants: int = 0
    survived: int = 0
    won: int = 0
    # mutants this site's own output killed, so the three sources sum over the
    # records of one attempt. Each is written where its counter can be other
    # than zero: the generator's cases always leave a record, the fuzz pass
    # runs only where a generator was written, and a round kills only where one
    # was asked
    killed: int = 0
    # what each round killed, in order, summing to `killed`. A list rather than
    # a field per round, since `ROUNDS` is what a corpus revises
    rounds: list[int] = Field(default_factory=list)
    # proposals the rounds put to the set, landed or not. `offered` less `won`
    # is what killed nothing, which is what a round wasted its call on
    offered: int = 0
    # the speedup search, where this site ran one
    separating: int | None = None
    unseparated: str | None = None

    @model_validator(mode="after")
    def _provenance_required(self) -> SiteOutcome:
        """A site writes an outcome only where it made a call, so there is no
        hand arm to exempt."""
        self.check_provenance(True)
        return self
