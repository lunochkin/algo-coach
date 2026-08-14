from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from algo_coach.schema.problem import ProblemDifficulty

Slug = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]*$")]


class Selector(BaseModel):
    """What a ladder resolves from: a technique and the filters narrowing it.

    Named fields rather than a filter map, so a resolver branches on what the
    type states. A new filter is a new optional field, which is additive.
    """

    technique: str
    # Empty is the whole range: an author who said nothing has not said "easy".
    difficulty: list[ProblemDifficulty] = Field(default_factory=list)
    size: int = Field(ge=1)  # a ladder of nothing teaches nothing


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
    def _template_slugs_are_unique(self) -> Card:
        unique_slugs([template.slug for template in self.templates])
        return self
