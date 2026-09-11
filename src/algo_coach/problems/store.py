from sqlalchemy import ColumnElement, select
from sqlalchemy.dialects.postgresql import insert

from algo_coach.problems.table import problems
from algo_coach.schema import Problem, ProblemStatus, RetirementReason
from algo_coach.storage import CONFIGURATION, Database, called, configurations, configured

# what a stored problem may still move: `corpus.md` gives the states
STATUS = {"status", "retired_reason"}


class ProblemStore:
    """Created once; only its status moves. A statement that says the wrong
    thing is retired and a new problem written, so the attempts stay with the
    record they were made against."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def put(self, record: Problem) -> None:
        if record.techniques:
            # `README.md`: aggregates are derived views, never stored truth
            raise ValueError(f"problem {record.id} carries a view; the store keeps the record")
        stored = self.get(record.id)
        if stored is not None and stored.model_dump(exclude=STATUS) != record.model_dump(
            exclude=STATUS
        ):
            raise ValueError(f"problem {record.id} is stored, and only its status moves")
        values = record.model_dump(exclude={"techniques", *CONFIGURATION})
        with self.root.begin() as conn:
            called(conn, [record])
            conn.execute(
                insert(problems)
                .values(values)
                .on_conflict_do_update(
                    index_elements=["id"], set_={name: values[name] for name in STATUS}
                )
            )

    def get(self, id: str) -> Problem | None:
        found = self._read(problems.c.id == id)
        return found[0] if found else None

    def all(self) -> list[Problem]:
        return self._read()

    def retire(self, problem_id: str, reason: RetirementReason) -> Problem:
        stored = self.get(problem_id)
        if stored is None:
            raise ValueError(f"no problem {problem_id}")
        # a sitting asks about each of its attempts in turn, so the second mark
        # on one problem is the loop repeating itself rather than a mistake
        if stored.status is ProblemStatus.RETIRED:
            return stored
        retired = Problem.model_validate(
            stored.model_dump() | {"status": ProblemStatus.RETIRED, "retired_reason": reason}
        )
        self.put(retired)
        return retired

    def _read(self, *where: ColumnElement[bool]) -> list[Problem]:
        with self.root.connect() as conn:
            rows = [
                dict(row)
                for row in conn.execute(
                    select(problems).where(*where).order_by(problems.c.id)
                ).mappings()
            ]
            known = configurations(conn, {row["call_id"] for row in rows})
        return [Problem.model_validate(configured(row, known)) for row in rows]
