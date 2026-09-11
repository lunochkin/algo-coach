from sqlalchemy import ColumnElement, delete, insert, select
from sqlalchemy.dialects.postgresql import insert as upsert

from algo_coach.log.table import sitting_pauses, sittings
from algo_coach.log.users import known
from algo_coach.schema import Sitting
from algo_coach.storage import Database


class SittingStore:
    """Revised as the sitting runs, and kept once it ends: how often practice
    is interrupted is readable here alone."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def put(self, record: Sitting) -> None:
        row = record.model_dump(exclude={"pauses"})
        with self.root.begin() as conn:
            known(conn, record.user_id)
            conn.execute(
                upsert(sittings).values(row).on_conflict_do_update(index_elements=["id"], set_=row)
            )
            # a sitting's pauses are few and move together, so they are
            # written again whole
            conn.execute(delete(sitting_pauses).where(sitting_pauses.c.sitting_id == record.id))
            if record.pauses:
                conn.execute(
                    insert(sitting_pauses),
                    [
                        one.model_dump() | {"sitting_id": record.id, "position": position}
                        for position, one in enumerate(record.pauses)
                    ],
                )

    def get(self, id: str) -> Sitting | None:
        found = self._read(sittings.c.id == id)
        return found[0] if found else None

    def all(self) -> list[Sitting]:
        return self._read()

    def running(self, user_id: str, problem_id: str) -> Sitting | None:
        found = self._read(
            sittings.c.user_id == user_id,
            sittings.c.problem_id == problem_id,
            sittings.c.ended_at.is_(None),
        )
        return found[0] if found else None

    def _read(self, *where: ColumnElement[bool]) -> list[Sitting]:
        with self.root.connect() as conn:
            rows = (
                conn.execute(select(sittings).where(*where).order_by(sittings.c.id))
                .mappings()
                .all()
            )
            held = conn.execute(
                select(sitting_pauses)
                .where(sitting_pauses.c.sitting_id.in_([row["id"] for row in rows]))
                .order_by(sitting_pauses.c.position)
            ).mappings()
            pauses: dict[str, list[dict[str, object]]] = {row["id"]: [] for row in rows}
            for one in held:
                pauses[one["sitting_id"]].append({"at": one["at"], "until": one["until"]})
        return [Sitting.model_validate(dict(row) | {"pauses": pauses[row["id"]]}) for row in rows]
