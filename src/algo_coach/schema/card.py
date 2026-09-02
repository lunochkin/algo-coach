from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.problem import ProblemDifficulty

Slug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]


class TemplateKind(StrEnum):
    CODE = "code"
    PROCEDURE = "procedure"  # a method's steps; written as code they would only look executable


class Selector(BaseModel):
    """What a ladder resolves from. Named fields rather than a filter map, so
    a new filter is an additive optional field."""

    technique: str
    difficulty: list[ProblemDifficulty] = Field(default_factory=list)  # empty is the whole range
    size: int = Field(ge=1)


def optional_budget(optional: list[bool]) -> None:
    """Rejects a second optional template, and a card that is all optional."""
    if sum(optional) > 1:
        raise ValueError("a card carries at most one optional template")
    if optional and all(optional):
        raise ValueError("a card needs a template that is not optional")


def unique_slugs(slugs: list[str]) -> None:
    """Rejects a repeated slug: a re-import would have no rule for which id to keep."""
    if len(set(slugs)) != len(slugs):
        raise ValueError("template slugs are unique within a card")


class Template(BaseModel):
    """One form reproduced from memory. The unit of recall."""

    id: str  # a recall attempt keys to it and outlives any edit
    slug: Slug  # authored; how a re-import finds the same template
    title: str
    trigger: str = Field(min_length=1)  # which form this is, where the card's says which technique
    notes: str | None = None  # this form alone; the card's brief carries what is technique-wide
    optional: bool = False  # the capstone: never rendered unless asked for by name
    speedup: bool = True  # false where the form is its own optimum, so no input separates it
    kind: TemplateKind = TemplateKind.CODE
    code: str  # whatever is blank-filled: a runnable unit, or the steps of a method


class Card(BaseModel):
    """Teaching content for one technique: forms to reproduce, and a selector."""

    id: str  # what a card run references
    slug: Slug  # authored; the idempotency key a re-seed matches on
    technique: str  # a bare string, as a code is everywhere: membership is a write-path check
    title: str
    trigger: str = Field(min_length=1)  # when to reach for the technique at all
    brief: str = Field(min_length=1)  # markdown; what to read before solving
    templates: list[Template] = Field(min_length=1)
    selector: Selector

    @model_validator(mode="after")
    def _templates_are_well_formed(self) -> Card:
        unique_slugs([template.slug for template in self.templates])
        optional_budget([template.optional for template in self.templates])
        return self
