from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from climb.schema.problem import ProblemDifficulty

Slug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]


class TemplateKind(StrEnum):
    CODE = "code"
    PROCEDURE = "procedure"  # a method's steps; written as code they would only look executable


class Selector(BaseModel):
    """What a ladder resolves from. Named fields rather than a filter map, so
    a new filter is an additive optional field."""

    model_config = ConfigDict(frozen=True)

    technique: str
    difficulty: list[ProblemDifficulty] = Field(
        default_factory=list[ProblemDifficulty]
    )  # empty is the whole range
    size: int = Field(ge=1)


def optional_budget(optional: list[bool]) -> None:
    """Rejects a second optional template, and a card that is all optional."""
    if sum(optional) > 1:
        raise ValueError("a card carries at most one optional template")
    if optional and all(optional):
        raise ValueError("a card needs a template that is not optional")


def unique_slugs(slugs: list[str]) -> None:
    """Rejects a repeated slug: a re-import would have no rule for which id to
    keep."""
    if len(set(slugs)) != len(slugs):
        raise ValueError("template slugs are unique within a card")


class Requirement(BaseModel):
    """One edge of the card graph: `content.md` gives what it asserts."""

    model_config = ConfigDict(frozen=True)

    card: Slug  # the required card
    template: Slug  # a core template of the required card
    used_by: Slug  # the template on this card using that form


def requirements_are_well_formed(
    slug: str, templates: list[str], requires: list[Requirement]
) -> None:
    """Refuses what one card alone shows wrong: the rest needs the graph."""
    if any(one.card == slug for one in requires):
        raise ValueError("a card does not require itself")
    if len({(one.card, one.template, one.used_by) for one in requires}) != len(requires):
        raise ValueError("a requirement is named once")
    unknown = sorted({one.used_by for one in requires} - set(templates))
    if unknown:
        raise ValueError(f"used_by names no template of this card: {', '.join(unknown)}")


class TemplateCase(BaseModel):
    """One case a reproduced form is checked against. The arguments are
    positional, and `solve` is the function they call."""

    model_config = ConfigDict(frozen=True)

    args: list[Any] = Field(default_factory=list[Any])  # positional; empty is legal
    expected: Any  # required: `None` is a value the form may return


class Template(BaseModel):
    """One form reproduced from memory. The unit of recall."""

    model_config = ConfigDict(frozen=True)

    id: str  # a recall attempt keys to it and outlives any edit
    slug: Slug  # authored; how a re-import finds the same template
    title: str
    trigger: str = Field(min_length=1)  # which form this is, where the card's says which technique
    notes: str | None = None  # this form alone; the card's brief carries what is technique-wide
    optional: bool = False  # a card is covered without it
    speedup: bool = True  # false where the form is its own optimum, so no input separates it
    kind: TemplateKind = TemplateKind.CODE
    code: str  # whatever is blank-filled: a runnable unit, or the steps of a method
    # the form's answer is a set: a case compares the returned list sorted, and
    # the order two correct reproductions emit it in is not a difference
    unordered: bool = False
    # what a recall is checked against; a template carrying none is read and
    # never recalled, as `content.md` gives it
    cases: list[TemplateCase] = Field(default_factory=list[TemplateCase])
    # the top-level definitions turning JSON into nodes and back, which a
    # judgement item neither shows nor mutates: `content.md`
    harness: list[str] = Field(default_factory=list[str])


class Card(BaseModel):
    """Teaching content for one technique: forms to reproduce, and a
    selector."""

    model_config = ConfigDict(frozen=True)

    id: str  # what a card run references
    slug: Slug  # authored; the idempotency key a re-seed matches on
    technique: str  # a bare string, as a code is everywhere: membership is a write-path check
    title: str
    trigger: str = Field(min_length=1)  # when to reach for the technique at all
    brief: str = Field(min_length=1)  # markdown; what to read before solving
    templates: list[Template] = Field(min_length=1)
    selector: Selector
    requires: list[Requirement] = Field(default_factory=list[Requirement])  # empty on a root

    @model_validator(mode="after")
    def _templates_are_well_formed(self) -> Card:
        slugs = [template.slug for template in self.templates]
        unique_slugs(slugs)
        optional_budget([template.optional for template in self.templates])
        requirements_are_well_formed(self.slug, slugs, self.requires)
        return self
