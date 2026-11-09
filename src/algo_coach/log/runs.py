"""The runs a user started, and the probes each was given."""

from collections.abc import Sequence

from sqlalchemy import ColumnElement, Connection, insert, select

from algo_coach.log.table import card_run_probes, card_runs
from algo_coach.log.users import known
from algo_coach.schema import CardRun, Probe
from algo_coach.storage import Database


class CardRunLog:
    """Append-only, as the log is: a later probe appends a row rather than
    rewriting the run it was given on."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def append(self, record: CardRun) -> None:
        with self.root.begin() as conn:
            known(conn, record.user_id)
            conn.execute(insert(card_runs).values(record.model_dump(exclude={"probes"})))
            self._probes(conn, record.id, record.probes, first=0)

    def offer(self, run_id: str, probe: Probe) -> None:
        """One probe more on a run already started. Later probes append, so
        what was offered and when stays readable."""
        with self.root.begin() as conn:
            taken = conn.execute(
                select(card_run_probes.c.position).where(card_run_probes.c.card_run_id == run_id)
            ).scalars()
            self._probes(conn, run_id, [probe], first=max(taken, default=-1) + 1)

    def all(self, user_id: str | None = None) -> list[CardRun]:
        if user_id is None:
            return self._read()
        return self._read(card_runs.c.user_id == user_id)

    def started(self, user_id: str, card_id: str) -> CardRun | None:
        """The run this user has open on this card, latest first. `None` where
        the card is unstarted, which is what the ladder is measured from."""
        found = self._read(card_runs.c.user_id == user_id, card_runs.c.card_id == card_id)
        return found[-1] if found else None

    def _probes(self, conn: Connection, run_id: str, probes: Sequence[Probe], first: int) -> None:
        if not probes:
            return
        conn.execute(
            insert(card_run_probes),
            [
                one.model_dump() | {"card_run_id": run_id, "position": first + place}
                for place, one in enumerate(probes)
            ],
        )

    def _read(self, *where: ColumnElement[bool]) -> list[CardRun]:
        with self.root.connect() as conn:
            rows = (
                conn.execute(select(card_runs).where(*where).order_by(card_runs.c.appended))
                .mappings()
                .all()
            )
            given = conn.execute(
                select(card_run_probes)
                .where(card_run_probes.c.card_run_id.in_([row["id"] for row in rows]))
                .order_by(card_run_probes.c.position)
            ).mappings()
            probes: dict[str, list[dict[str, object]]] = {row["id"]: [] for row in rows}
            for one in given:
                probes[one["card_run_id"]].append(
                    {"problem_id": one["problem_id"], "assigned_at": one["assigned_at"]}
                )
        return [CardRun.model_validate(dict(row) | {"probes": probes[row["id"]]}) for row in rows]
