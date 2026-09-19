"""The templates a user reproduced from memory, and how each one went."""

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import ColumnElement, insert, select

from algo_coach.log.table import recall_attempt_case_results, recall_attempts
from algo_coach.log.users import known
from algo_coach.schema import RecallAttempt
from algo_coach.standing import latest_by
from algo_coach.storage import Database


class RecallLog:
    """Append-only: a second reproduction of one form is a second record, and
    neither supersedes the other."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def append(self, record: RecallAttempt) -> None:
        with self.root.begin() as conn:
            known(conn, record.user_id)
            conn.execute(insert(recall_attempts).values(record.model_dump(exclude={"results"})))
            if record.results:
                conn.execute(
                    insert(recall_attempt_case_results),
                    [
                        one.model_dump() | {"recall_attempt_id": record.id, "position": position}
                        for position, one in enumerate(record.results)
                    ],
                )

    def all(
        self, user_id: str | None = None, *, since: datetime | None = None
    ) -> list[RecallAttempt]:
        """`since` reads the reproductions written at or after it, so a rate is
        counted in the query rather than over the user's whole log."""
        conditions: list[ColumnElement[bool]] = []
        if user_id is not None:
            conditions.append(recall_attempts.c.user_id == user_id)
        if since is not None:
            conditions.append(recall_attempts.c.created_at >= since)
        return self._read(*conditions)

    def for_card(self, user_id: str, card_id: str) -> list[RecallAttempt]:
        return self._read(
            recall_attempts.c.user_id == user_id, recall_attempts.c.card_id == card_id
        )

    def _read(self, *where: ColumnElement[bool]) -> list[RecallAttempt]:
        with self.root.connect() as conn:
            rows = (
                conn.execute(
                    select(recall_attempts).where(*where).order_by(recall_attempts.c.appended)
                )
                .mappings()
                .all()
            )
            ran = conn.execute(
                select(recall_attempt_case_results)
                .where(
                    recall_attempt_case_results.c.recall_attempt_id.in_([row["id"] for row in rows])
                )
                .order_by(recall_attempt_case_results.c.position)
            ).mappings()
            results: dict[str, list[dict[str, object]]] = {row["id"]: [] for row in rows}
            for one in ran:
                results[one["recall_attempt_id"]].append(
                    {key: value for key, value in one.items() if key != "recall_attempt_id"}
                )
        return [
            RecallAttempt.model_validate(dict(row) | {"results": results[row["id"]]})
            for row in rows
        ]


# every earlier reproduction stays in the log, and the card reports the last
def latest_recalls(attempts: Iterable[RecallAttempt]) -> dict[str, RecallAttempt]:
    """The last reproduction of each template."""
    return latest_by(attempts, lambda one: one.template_id)
