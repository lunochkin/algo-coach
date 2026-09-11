from typing import Any

from sqlalchemy import ColumnElement, Connection, delete, select, update
from sqlalchemy.dialects.postgresql import insert

from algo_coach.cards.table import card_templates, cards
from algo_coach.schema import Card
from algo_coach.storage import Database


class CardStore:
    """Revised in place: a re-seed refreshes a card by its slug and keeps every
    template's id, which the problems written for it name."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def put(self, record: Card) -> None:
        values = record.model_dump(exclude={"templates", "selector"}) | {
            f"selector_{name}": value for name, value in record.selector.model_dump().items()
        }
        with self.root.begin() as conn:
            conn.execute(
                insert(cards)
                .values(values)
                .on_conflict_do_update(index_elements=["id"], set_=values)
            )
            self._templates(conn, record)

    def get(self, id: str) -> Card | None:
        found = self._read(cards.c.id == id)
        return found[0] if found else None

    def all(self) -> list[Card]:
        return self._read()

    def by_slug(self, slug: str) -> Card | None:
        found = self._read(cards.c.slug == slug)
        return found[0] if found else None

    def for_technique(self, technique: str) -> list[Card]:
        return sorted(self._read(cards.c.technique == technique), key=lambda one: one.slug)

    def _templates(self, conn: Connection, record: Card) -> None:
        # upserted by id rather than replaced: a problem names its template, and
        # a deleted row would refuse the problem pointing at it
        kept = [one.id for one in record.templates]
        conn.execute(
            delete(card_templates).where(
                card_templates.c.card_id == record.id, card_templates.c.id.not_in(kept)
            )
        )
        # out of the way first, so a reordering never holds two templates at one
        # position of one card
        conn.execute(
            update(card_templates)
            .where(card_templates.c.card_id == record.id)
            .values(position=-card_templates.c.position - 1)
        )
        for position, template in enumerate(record.templates):
            values = template.model_dump() | {"card_id": record.id, "position": position}
            conn.execute(
                insert(card_templates)
                .values(values)
                .on_conflict_do_update(index_elements=["id"], set_=values)
            )

    def _read(self, *where: ColumnElement[bool]) -> list[Card]:
        with self.root.connect() as conn:
            rows = conn.execute(select(cards).where(*where).order_by(cards.c.id)).mappings().all()
            ids = [row["id"] for row in rows]
            held = conn.execute(
                select(card_templates)
                .where(card_templates.c.card_id.in_(ids))
                .order_by(card_templates.c.position)
            ).mappings()
            templates: dict[str, list[dict[str, Any]]] = {id: [] for id in ids}
            for one in held:
                templates[one["card_id"]].append(dict(one))
        return [
            Card.model_validate(
                {key: value for key, value in row.items() if not key.startswith("selector_")}
                | {
                    "selector": {
                        "technique": row["selector_technique"],
                        "difficulty": row["selector_difficulty"],
                        "size": row["selector_size"],
                    },
                    "templates": templates[row["id"]],
                }
            )
            for row in rows
        ]
