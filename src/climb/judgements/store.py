from sqlalchemy import ColumnElement, insert, select, update

from climb.judgements.table import judgement_items
from climb.schema import ItemStatus, JudgementItem
from climb.storage import Database


class ItemStore:
    """Items are appended and never edited; a retirement moves the status."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def add(self, items: list[JudgementItem]) -> None:
        if not items:
            return
        with self.root.begin() as conn:
            conn.execute(insert(judgement_items), [one.model_dump() for one in items])

    def all(self) -> list[JudgementItem]:
        return self._read()

    def served(self) -> list[JudgementItem]:
        return self._read(judgement_items.c.status == ItemStatus.SERVED)

    def retire(self, ids: list[str]) -> None:
        if not ids:
            return
        with self.root.begin() as conn:
            conn.execute(
                update(judgement_items)
                .where(judgement_items.c.id.in_(ids))
                .values(status=ItemStatus.RETIRED)
            )

    def _read(self, *where: ColumnElement[bool]) -> list[JudgementItem]:
        with self.root.connect() as conn:
            rows = conn.execute(
                select(judgement_items).where(*where).order_by(judgement_items.c.id)
            ).mappings()
            return [JudgementItem.model_validate(dict(one)) for one in rows]
