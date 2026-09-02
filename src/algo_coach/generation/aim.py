"""What a run is written for: the core templates no stored solution displays.

Aimed at the gaps rather than left to the selector, which fills a ladder from
whatever the corpus holds and never asks for the form that is missing.
"""

from collections.abc import Iterable

from pydantic import BaseModel

from algo_coach.matches import coverage, uncovered
from algo_coach.schema import Card, Problem, Solution, Template, TemplateMatch


class Target(BaseModel):
    """One template a generation run writes for, beside the card it is on: a
    brief is built from both."""

    card: Card
    template: Template


def targets(
    cards: Iterable[Card],
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    matches: Iterable[TemplateMatch],
) -> list[Target]:
    """A target per gap, in the order the gap report lists them."""
    cards = list(cards)
    by_slug = {card.slug: card for card in cards}
    aimed = []
    for gap in uncovered(coverage(cards, problems, solutions, matches)):
        card = by_slug[gap.card_slug]
        template = next(one for one in card.templates if one.id == gap.template_id)
        aimed.append(Target(card=card, template=template))
    return aimed
