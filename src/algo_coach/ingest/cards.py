from collections.abc import Iterable, Mapping

from pydantic import ValidationError

from algo_coach.cards import CardStore
from algo_coach.ingest.result import CardSeedResult, Rejected, reason
from algo_coach.mint import new_id
from algo_coach.schema import Card, CardSeed, Template
from algo_coach.techniques import is_known


def seed_cards(records: Iterable[Mapping], *, store: CardStore) -> CardSeedResult:
    """Validate authored cards, mint what identifies them, upsert each one.

    Records rather than paths: where the content lives is the caller's, so
    moving it behind a private repo changes the reader and not this.

    The rules, in the order they bite:

    - `CardSeed` carries no id, so an author supplies none; the card's and each
      template's are minted here.
    - The slug is the idempotency key, at both levels: a known card slug
      refreshes and counts as `updated`, and a template keeps the id its slug
      already had. A new slug is a new card, and the old one stays.
    - The technique is checked against the vocabulary, on the card and on its
      selector — the one write path that could introduce an unrecognised code.
    - Rejection is per record, by index, as at every other boundary.
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
