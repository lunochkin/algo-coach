from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.problem import ProblemDifficulty

Slug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]


class TemplateKind(StrEnum):
    """What a template reproduces.

    Usually code. Sometimes what has to come back cold is a method rather than
    a function: the steps for turning an unseen problem into a state and a
    recurrence. Written out as code, such a procedure would be a checklist that
    only looks executable.
    """

    CODE = "code"
    PROCEDURE = "procedure"


class Selector(BaseModel):
    """What a ladder resolves from: a technique and the filters narrowing it.

    Named fields rather than a filter map, so a resolver branches on what the
    type states. A new filter is a new optional field, which is additive.
    """

    technique: str
    # Empty is the whole range: an author who said nothing has not said "easy".
    difficulty: list[ProblemDifficulty] = Field(default_factory=list)
    size: int = Field(ge=1)  # a ladder of nothing teaches nothing


def optional_budget(optional: list[bool]) -> None:
    """At most one optional template, and never every template.

    An optional template is the hard capstone a card may carry — reached by
    asking for it, not by studying the card. More than one and "optional" is
    just a second tier of ordinary work; all of them and the card teaches
    nothing until asked.
    """
    if sum(optional) > 1:
        raise ValueError("a card carries at most one optional template")
    if optional and all(optional):
        raise ValueError("a card needs a template that is not optional")


def unique_slugs(slugs: list[str]) -> None:
    """Two templates sharing a slug leave a re-import with no rule for which
    minted id to keep, and a recall history split across both.

    Checked on the authored payload as well as the record: a card rejected
    only at import costs an authoring pass to learn what a validator knew.
    """
    if len(set(slugs)) != len(slugs):
        raise ValueError("template slugs are unique within a card")


class Template(BaseModel):
    """One form reproduced from memory. The unit of recall, since a card's
    forms are learned and lost separately."""

    id: str  # engine-minted; a recall attempt keys to it and outlives any edit
    slug: Slug  # authored; how a re-import finds the same template
    title: str
    # Which form this is, where the card's cue says to reach for the technique
    # at all. Recall is per template, so the cue that has to fire is too — a
    # card-level one would be right about the technique and silent about which
    # of its forms the problem is asking for.
    trigger: str = Field(min_length=1)
    # What to read about this form and nothing else: when it applies, its
    # unlock, its variations. Absent where the trigger says all there is —
    # the card's brief carries what is technique-wide, and a reader studying
    # one form should not have to scan the prose of the other three.
    notes: str | None = None
    # Outside the card's default study set: never rendered unless it is asked
    # for by name. A capstone the user may want to derive rather than read, so
    # the card holds the answer and does not volunteer it.
    optional: bool = False
    # Whether this form beats the naive solution the technique replaces. Nearly
    # always true, so the exception says so: backtracking and exhaustive search
    # are their own optimum, and no input separates them from a reference.
    # Generation searches for that separating input only where it is claimed,
    # and a missing one is a defect only there.
    speedup: bool = True
    kind: TemplateKind = TemplateKind.CODE
    # Whatever is blank-filled: a runnable unit, or the numbered steps of a
    # method. The field keeps its name because code is what it holds nearly
    # always, and a second field would leave every reader asking which is set.
    code: str


class Card(BaseModel):
    """Teaching content for one technique: what to reproduce from memory, and
    the selector the problems to solve are drawn by.

    Names no problem. Ids are minted per engine, so a card holding them would
    mean nothing in another store — the selector is what ships, and the ladder
    is derived from the corpus at import.

    Several per technique: granularity follows teaching, and mastery is
    estimated per technique, so nothing makes a technique's card unique.

    The technique is a bare string, as a code is everywhere else. Membership is
    checked on the write path, or a card seeded before a code was retired would
    stop being readable by its own schema.
    """

    id: str  # engine-minted; what a card run references
    slug: Slug  # authored; the idempotency key a re-seed matches on
    technique: str
    title: str
    # When to reach for the technique at all, apart from the rest of the prose:
    # a probe asks exactly this — whether it is recognised unprompted — so it is
    # shown and withheld on its own. Which form to reach for is the template's.
    trigger: str = Field(min_length=1)
    brief: str = Field(min_length=1)  # markdown; what to read before solving
    templates: list[Template] = Field(min_length=1)
    selector: Selector

    @model_validator(mode="after")
    def _templates_are_well_formed(self) -> Card:
        unique_slugs([template.slug for template in self.templates])
        optional_budget([template.optional for template in self.templates])
        return self
