from typing import Any

from sqlalchemy import ColumnElement, Connection, Table, delete, select, update
from sqlalchemy.dialects.postgresql import insert

from algo_coach.cards.table import card_requirements, card_templates, cards, template_cases
from algo_coach.schema import Card
from algo_coach.storage import Database


class CardStore:
    """Revised in place: a re-seed refreshes a card by its slug and keeps every
    template's id, which the problems written for it name."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def put(self, record: Card) -> None:
        self.put_all([record])

    def put_all(self, records: list[Card]) -> None:
        """One transaction and one batched statement per table, the edges last:
        a card may require another card the same batch adds. Through a tunnel
        each statement waits a round trip, so none is sent per row."""
        if not records:
            return
        ids = [one.id for one in records]
        kept = [template.id for one in records for template in one.templates]
        with self.root.begin() as conn:
            # cleared first, so no edge holds a template a re-seed removes
            conn.execute(delete(card_requirements).where(card_requirements.c.card_id.in_(ids)))
            _upsert(
                conn,
                cards,
                [
                    one.model_dump(exclude={"templates", "selector", "requires"})
                    | {
                        f"selector_{name}": value
                        for name, value in one.selector.model_dump().items()
                    }
                    for one in records
                ],
            )
            # upserted by id rather than replaced: a problem names its template,
            # and a deleted row would refuse the problem pointing at it
            conn.execute(
                delete(card_templates).where(
                    card_templates.c.card_id.in_(ids), card_templates.c.id.not_in(kept)
                )
            )
            # out of the way first, so a reordering never holds two templates at
            # one position of one card
            conn.execute(
                update(card_templates)
                .where(card_templates.c.card_id.in_(ids))
                .values(position=-card_templates.c.position - 1)
            )
            _upsert(
                conn,
                card_templates,
                [
                    template.model_dump(exclude={"cases"})
                    | {"card_id": one.id, "position": position}
                    for one in records
                    for position, template in enumerate(one.templates)
                ],
            )
            # a template's cases, replaced whole: no record points at one, so a
            # re-seed rewrites the set the author last wrote
            conn.execute(delete(template_cases).where(template_cases.c.template_id.in_(kept)))
            _insert(
                conn,
                template_cases,
                [
                    {"template_id": template.id, "position": position, **case.model_dump()}
                    for one in records
                    for template in one.templates
                    for position, case in enumerate(template.cases)
                ],
            )
            _insert(
                conn,
                card_requirements,
                [
                    {"card_id": one.id, "position": position, **edge.model_dump()}
                    for one in records
                    for position, edge in enumerate(one.requires)
                ],
            )

    def get(self, id: str) -> Card | None:
        found = self._read(cards.c.id == id)
        return found[0] if found else None

    def all(self) -> list[Card]:
        return self._read()

    def by_slug(self, slug: str) -> Card | None:
        found = self._read(cards.c.slug == slug)
        return found[0] if found else None

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
                templates[one["card_id"]].append(dict(one) | {"cases": []})
            authored = conn.execute(
                select(template_cases)
                .where(
                    template_cases.c.template_id.in_(
                        [one["id"] for group in templates.values() for one in group]
                    )
                )
                .order_by(template_cases.c.position)
            ).mappings()
            edges = conn.execute(
                select(card_requirements)
                .where(card_requirements.c.card_id.in_(ids))
                .order_by(card_requirements.c.position)
            ).mappings()
            requires: dict[str, list[dict[str, Any]]] = {id: [] for id in ids}
            for edge in edges:
                requires[edge["card_id"]].append(
                    {"card": edge["card"], "template": edge["template"], "used_by": edge["used_by"]}
                )
            by_template = {one["id"]: one["cases"] for group in templates.values() for one in group}
            for case in authored:
                by_template[case["template_id"]].append(
                    {"args": case["args"], "expected": case["expected"]}
                )
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
                    "requires": requires[row["id"]],
                }
            )
            for row in rows
        ]


def _upsert(conn: Connection, table: Table, rows: list[dict[str, Any]]) -> None:
    """Every row in one statement, each refreshed where its id is stored."""
    if not rows:
        return
    statement = insert(table)
    columns = [name for name in rows[0] if name != "id"]
    conn.execute(
        statement.on_conflict_do_update(
            index_elements=["id"], set_={name: statement.excluded[name] for name in columns}
        ),
        rows,
    )


def _insert(conn: Connection, table: Table, rows: list[dict[str, Any]]) -> None:
    if rows:
        conn.execute(insert(table), rows)
