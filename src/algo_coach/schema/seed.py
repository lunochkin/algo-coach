"""What an author writes. The engine's own record is `Card`."""

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.card import (
    Selector,
    Slug,
    TemplateKind,
    optional_budget,
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


class CardSeed(BaseModel):
    """One authored card. The engine owns `id`, here and on every template."""

    slug: Slug
    technique: str
    title: str
    trigger: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    templates: list[TemplateSeed] = Field(min_length=1)
    selector: Selector

    @model_validator(mode="after")
    def _templates_are_well_formed(self) -> CardSeed:
        unique_slugs([template.slug for template in self.templates])
        optional_budget([template.optional for template in self.templates])
        return self
