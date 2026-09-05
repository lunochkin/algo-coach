"""One attempt at writing a problem, held as it is written.

Working state rather than a log: a draft is revised in place and cleared at
landing. `flows.md` gives the states and what a resume may not do.
"""

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from algo_coach.schema.case import ExpectedSource
from algo_coach.schema.outcome import Discard
from algo_coach.schema.problem import ProblemDifficulty
from algo_coach.schema.provenance import MachineProvenance


class WritingState(StrEnum):
    """How far a problem has been written. One state per step that can fail, in
    the order `flows.md` gives; `landed` is where `ProblemStatus` starts."""

    DRAFTED = "drafted"
    CHECKED = "checked"
    REFERENCED = "referenced"
    AGREED = "agreed"
    BUILT = "built"
    PACED = "paced"
    SEARCHED = "searched"
    HARDENED = "hardened"
    LANDED = "landed"
    REJECTED = "rejected"  # terminal; `gate` says what reached it


class DraftCase(BaseModel):
    """One case as the generator wrote it: the arguments and what `solve` must
    return."""

    # no id, no problem and no `expected_from`: none of the three exists until
    # the problem lands, and the reference recomputes `expected` before it does
    args: list[Any]
    expected: Any

    @field_validator("args", "expected", mode="before")
    @classmethod
    def _decoded(cls, value: Any) -> Any:
        # strict structured output cannot express an unconstrained JSON value,
        # so the two arrive as text and are checked here, not by the provider
        return json.loads(value) if isinstance(value, str) else value


class SettledCase(BaseModel):
    """One case a run established: whose answer it carries, and the call that
    proposed the arguments."""

    model_config = ConfigDict(frozen=True)

    # neither a `TestCase`, which needs a problem id, nor a `DraftCase`, whose
    # `expected` was declared rather than established by a run
    args: list[Any]
    expected: Any
    expected_from: ExpectedSource
    # the configuration rather than the call: the `TestCase` this becomes
    # copies it, and a call carries its prompt whole, which every case of one
    # draft would then hold a copy of
    written: MachineProvenance
    round: int | None = 0  # as `TestCase.round`


class Draft(BaseModel):
    """What the steps of one attempt produced and no local run re-derives.

    The mutants, the survivors and the loop's counters are not here: a tree
    walk enumerates the first two and the site outcomes of this id carry the
    third.
    """

    id: str = Field(min_length=1)  # the writing id the site outcomes group under
    state: WritingState = WritingState.DRAFTED
    # what rejected the answer, as the same gate on the site whose output made
    # it decidable. A field rather than a record: nothing but the run writes it
    gate: Discard | None = None
    # the problem this draft landed as, absent until it did. A crash between
    # landing and clearing leaves a draft naming one, which is what tells the
    # next run to clear it rather than write the problem a second time
    problem_id: str | None = Field(default=None, min_length=1)
    # the form the brief named, absent where a technique brief named none, as
    # on `SiteOutcome`. A resume reads the template's `speedup`, and a sweep
    # over the store has nothing else to find it from
    template_id: str | None = Field(default=None, min_length=1)

    # drafted: one call wrote all five, so a draft exists only once they do
    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    canonical: str = Field(min_length=1)
    declared: list[DraftCase] = Field(min_length=1)
    difficulty: ProblemDifficulty
    # referenced: the second solution, written from the statement alone
    reference: str | None = Field(default=None, min_length=1)
    # agreed: what the two solutions settled, where `declared` holds what the
    # generator's own call said each case returns
    cases: list[SettledCase] = Field(default_factory=list)
    # built: the code that builds an input of a given size, and the largest
    # size the statement admits
    builder: str | None = Field(default=None, min_length=1)
    largest: int | None = Field(default=None, gt=0)
    # paced: the clock the search measures the canonical against, written as the
    # approach the form replaces. Absent where no speedup is claimed
    naive: str | None = Field(default=None, min_length=1)
    # searched: the case at the size the naive solution stops fitting, absent
    # where the form is its own optimum or nothing separated
    separating: SettledCase | None = None
    # why the search stored no case, as the inputs site records it. A resume
    # reads it: the exits a held draft leaves by differ by what stopped it
    unseparated: str | None = Field(default=None, min_length=1)
    # hardened: what the loop appended to the set — the inputs the fuzz pass
    # kept, then the cases the rounds won. Neither lands where it killed
    # nothing, so this is what the step was paid for
    won: list[SettledCase] = Field(default_factory=list)

    # the configuration each step ran at, copied as its call returned. A resume
    # starts at the first step whose configuration or digest moved, which is
    # why both are held here rather than only the outputs
    generator: MachineProvenance | None = None
    blind: MachineProvenance | None = None
    inputs: MachineProvenance | None = None  # the builder and the search it fed
    clock: MachineProvenance | None = None  # the naive solution a search measures against
    discrimination: MachineProvenance | None = None

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

    @model_validator(mode="after")
    def _landing_names_the_problem(self) -> Draft:
        """Rejects a landed draft naming no problem, and a problem named by one
        that has not landed."""
        landed = self.state is WritingState.LANDED
        if landed and self.problem_id is None:
            raise ValueError("a landed draft names the problem_id it became")
        if not landed and self.problem_id is not None:
            raise ValueError(f"a {self.state} draft carries no problem_id")
        return self

    @model_validator(mode="after")
    def _the_builder_carries_its_bound(self) -> Draft:
        """One call returned both, and a search asking for a size the statement
        excludes is what a bound without code cannot stop."""
        if (self.builder is None) != (self.largest is None):
            raise ValueError("a builder is stored with the bound its call reported")
        return self

    @model_validator(mode="after")
    def _each_step_copies_a_whole_configuration(self) -> Draft:
        """A step whose configuration is partly unknown could not be compared
        with the one a resume would run."""
        for site in ("generator", "blind", "inputs", "clock", "discrimination"):
            copied = getattr(self, site)
            if copied is not None:
                copied.check_provenance(True)
        return self
