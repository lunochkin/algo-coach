from collections.abc import Iterable, Mapping

from pydantic import BaseModel, Field, ValidationError

from algo_coach.cards.store import CardStore
from algo_coach.mint import new_id
from algo_coach.schema import Card, CardSeed, Template
from algo_coach.techniques import is_known


class Rejected(BaseModel):
    index: int  # position in the seeded batch, so the author can find the file
    reason: str


class CardSeedResult(BaseModel):
    ingested: int = 0
    updated: int = 0  # a slug already seeded; the card refreshes, its id stays
    rejected: list[Rejected] = Field(default_factory=list)


def reason(exc: ValidationError) -> str:
    # Flattened: pydantic renders a multi-line block, which a caller parsing
    # JSON cannot use.
    return "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in exc.errors()
    )


def seed_cards(records: Iterable[Mapping], *, store: CardStore) -> CardSeedResult:
    """Validate authored cards, mint what identifies them, upsert each one.

    Records rather than paths: the caller owns where the content lives. The
    slug is the idempotency key at both levels, and rejection is per record.
    """
    result = CardSeedResult()

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

        existing = store.by_slug(seed.slug)
        minted = {template.slug: template.id for template in existing.templates} if existing else {}
        card = Card(
            **seed.model_dump(exclude={"templates"}),
            id=existing.id if existing else new_id(),
            templates=[
                Template(**template.model_dump(), id=minted.get(template.slug) or new_id())
                for template in seed.templates
            ],
        )

        store.put(card)
        if existing:
            result.updated += 1
        else:
            result.ingested += 1

    return result
