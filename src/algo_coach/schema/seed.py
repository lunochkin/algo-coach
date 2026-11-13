"""What an author writes. The engine's own record is `Card`."""

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.card import (
    Requirement,
    Selector,
    Slug,
    TemplateCase,
    TemplateKind,
    optional_budget,
    requirements_are_well_formed,
    unique_slugs,
)


class TemplateSeed(BaseModel):
    """One form to reproduce from memory, before it has an id."""

    slug: Slug
    title: str
    trigger: str = Field(min_length=1)
    notes: str | None = None
    optional: bool = False
    speedup: bool = True
    kind: TemplateKind = TemplateKind.CODE
    code: str
    unordered: bool = False
    cases: list[TemplateCase] = Field(default_factory=list[TemplateCase])
    harness: list[str] = Field(default_factory=list[str])
    # the surviving mutants the author judged equivalent to the form, as `card
    # check` names them. Authoring alone: the seed stores none
    equivalent: list[str] = Field(default_factory=list[str])


class CardSeed(BaseModel):
    """One authored card. The engine owns `id`, here and on every template."""

    slug: Slug
    technique: str
    title: str
    trigger: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    templates: list[TemplateSeed] = Field(min_length=1)
    selector: Selector
    requires: list[Requirement] = Field(default_factory=list[Requirement])

    @model_validator(mode="after")
    def _templates_are_well_formed(self) -> CardSeed:
        slugs = [template.slug for template in self.templates]
        unique_slugs(slugs)
        optional_budget([template.optional for template in self.templates])
        requirements_are_well_formed(self.slug, slugs, self.requires)
        return self
