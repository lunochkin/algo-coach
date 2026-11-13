from collections.abc import Iterable, Iterator, Mapping
from typing import Any

from pydantic import BaseModel, ValidationError

from algo_coach.cards.graph import broken
from algo_coach.cards.store import CardStore
from algo_coach.ids import new_id
from algo_coach.schema import Card, CardSeed, Template
from algo_coach.techniques import is_known


class Rejected(BaseModel):
    index: int  # position in the seeded batch, so the author can find the file
    reason: str


class CardSeedResult(BaseModel):
    ingested: int = 0
    updated: int = 0  # a slug already seeded; the card refreshes, its id stays
    rejected: list[Rejected] = []


def reason(exc: ValidationError) -> str:
    # Flattened: pydantic renders a multi-line block, which a caller parsing
    # JSON cannot use.
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    )


def seed_cards(records: Iterable[Mapping[str, Any]], *, store: CardStore) -> CardSeedResult:
    """Validate authored cards, mint what identifies them, upsert each one.

    Records rather than paths: the caller owns where the content lives. The
    slug is the idempotency key at both levels, and rejection is per record.
    """
    result = CardSeedResult()
    accepted: dict[str, tuple[int, CardSeed]] = {}

    for index, raw in enumerate(records):
        try:
            seed = CardSeed.model_validate(raw)
        except ValidationError as exc:
            result.rejected.append(Rejected(index=index, reason=reason(exc)))
            continue

        unknown = dict.fromkeys(
            code for code in (seed.technique, seed.selector.technique) if not is_known(code)
        )
        if unknown:
            result.rejected.append(
                Rejected(index=index, reason=f"unknown technique code(s): {', '.join(unknown)}")
            )
            continue
        if seed.slug in accepted:
            result.rejected.append(Rejected(index=index, reason=f"seeded twice: {seed.slug}"))
            continue
        accepted[seed.slug] = (index, seed)

    stored = {card.slug: card for card in store.all()}
    for slug, why in refused(stored, {slug: seed for slug, (_, seed) in accepted.items()}):
        result.rejected.append(Rejected(index=accepted.pop(slug)[0], reason=why))
    result.rejected.sort(key=lambda one: one.index)

    minted: list[Card] = []
    for _, seed in accepted.values():
        existing = stored.get(seed.slug)
        ids = {template.slug: template.id for template in existing.templates} if existing else {}
        minted.append(
            Card(
                **seed.model_dump(exclude={"templates"}),
                id=existing.id if existing else new_id(),
                templates=[
                    Template(**template.model_dump(), id=ids.get(template.slug) or new_id())
                    for template in seed.templates
                ],
            )
        )
        if existing:
            result.updated += 1
        else:
            result.ingested += 1
    store.put_all(minted)

    return result


def refused(stored: Mapping[str, Card], seeds: Mapping[str, CardSeed]) -> Iterator[tuple[str, str]]:
    """The seeds the card graph refuses, each with why. A refused seed leaves
    its stored card standing, so the graph is checked again without it."""
    left = dict(seeds)
    while True:
        graph: dict[str, Card | CardSeed] = {**stored, **left}
        blamed: dict[str, str] = {}
        for slug, why in broken(graph).items():
            if slug in left:
                blamed[slug] = why
                continue
            # a stored card the batch broke: the seed it requires is refused
            for one in graph[slug].requires:
                if one.card in left:
                    blamed.setdefault(one.card, f"{slug} requires {one.card}/{one.template}")
        if not blamed:
            return
        for slug, why in blamed.items():
            del left[slug]
            yield slug, why
