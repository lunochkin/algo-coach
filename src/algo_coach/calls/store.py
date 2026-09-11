from sqlalchemy import insert, select

from algo_coach.calls.table import calls
from algo_coach.schema import Call
from algo_coach.storage import Database


class CallLog:
    """What was asked of a model and what returned. No index by hash: several
    calls can share one prompt."""

    def __init__(self, root: Database) -> None:
        self.root = root
        # what this instance appended, so a caller reads its own tail without
        # loading the log
        self.appended: list[Call] = []

    def append(self, record: Call) -> None:
        with self.root.engine.begin() as conn:
            conn.execute(insert(calls).values(record.model_dump()))
        self.appended.append(record)

    def all(self) -> list[Call]:
        with self.root.engine.connect() as conn:
            rows = conn.execute(select(calls).order_by(calls.c.appended)).mappings()
            return [Call.model_validate(dict(row)) for row in rows]
