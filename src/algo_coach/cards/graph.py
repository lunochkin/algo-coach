"""The card graph's checks across cards: `content.md`, The card graph."""

from collections.abc import Iterable, Mapping

from algo_coach.schema import Card, CardSeed


def broken(cards: Mapping[str, Card | CardSeed]) -> dict[str, str]:
    """Each card, by slug, whose requirements the graph refuses, with why."""
    reasons: dict[str, str] = {}
    for slug, card in cards.items():
        for one in card.requires:
            required = cards.get(one.card)
            template = (
                next((each for each in required.templates if each.slug == one.template), None)
                if required
                else None
            )
            if required is None:
                reasons[slug] = f"requires an unknown card: {one.card}"
            elif template is None:
                reasons[slug] = f"requires an unknown template: {one.card}/{one.template}"
            elif template.optional:
                reasons[slug] = f"requires an optional template: {one.card}/{one.template}"
            else:
                continue
            break
    for slug in on_a_cycle(cards):
        reasons.setdefault(slug, "on a cycle of requirements")
    return reasons


def on_a_cycle(cards: Mapping[str, Card | CardSeed]) -> set[str]:
    edges = {
        slug: {one.card for one in card.requires if one.card in cards}
        for slug, card in cards.items()
    }
    # a card is on a cycle where it reaches itself
    return {slug for slug in edges if slug in reached(edges, slug)}


def reached(edges: Mapping[str, set[str]], start: str) -> set[str]:
    seen: set[str] = set()
    stack = list(edges[start])
    while stack:
        one = stack.pop()
        if one not in seen:
            seen.add(one)
            stack.extend(edges[one])
    return seen


def depths(cards: Iterable[Card]) -> dict[str, int]:
    """Each card's depth, by slug: the longest chain of requirements below it.
    The seed refused every cycle, so the walk ends."""
    by_slug = {card.slug: card for card in cards}
    found: dict[str, int] = {}

    def depth(slug: str) -> int:
        if slug not in found:
            below = [depth(one.card) for one in by_slug[slug].requires if one.card in by_slug]
            found[slug] = 1 + max(below) if below else 0
        return found[slug]

    for slug in by_slug:
        depth(slug)
    return found
