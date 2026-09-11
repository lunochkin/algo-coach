from typing import Any

from sqlalchemy import ColumnElement, insert, select

from algo_coach.schema import Verification
from algo_coach.storage import Database
from algo_coach.verifications.table import verification_case_results, verifications


class VerificationLog:
    """Verification runs; neither of two runs of one solution supersedes the
    other."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def append(self, record: Verification) -> None:
        with self.root.begin() as conn:
            conn.execute(insert(verifications).values(record.model_dump(exclude={"results"})))
            if record.results:
                conn.execute(
                    insert(verification_case_results),
                    [
                        one.model_dump() | {"verification_id": record.id, "position": position}
                        for position, one in enumerate(record.results)
                    ],
                )

    def all(self) -> list[Verification]:
        return self._read()

    def verifications(self) -> list[Verification]:
        return self.all()

    def for_solution(self, solution_id: str) -> list[Verification]:
        return self._read(verifications.c.solution_id == solution_id)

    def _read(self, *where: ColumnElement[bool]) -> list[Verification]:
        with self.root.connect() as conn:
            runs = (
                conn.execute(select(verifications).where(*where).order_by(verifications.c.appended))
                .mappings()
                .all()
            )
            results: dict[str, list[dict[str, Any]]] = {run["id"]: [] for run in runs}
            held = conn.execute(
                select(verification_case_results)
                .where(verification_case_results.c.verification_id.in_(results))
                .order_by(verification_case_results.c.position)
            ).mappings()
            for one in held:
                results[one["verification_id"]].append(dict(one))
        return [
            Verification.model_validate(dict(run) | {"results": results[run["id"]]}) for run in runs
        ]
