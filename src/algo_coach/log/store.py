from typing import Any

from sqlalchemy import ColumnElement, Table, insert, select

from algo_coach.log.table import (
    attempt_claims,
    attempt_verification_case_results,
    attempt_verifications,
    attempts,
    diagnoses,
    self_labels,
)
from algo_coach.log.users import known
from algo_coach.schema import Attempt, AttemptClaim, AttemptVerification, Diagnosis, SelfLabel
from algo_coach.storage import Database, Log


class AttemptLog:
    """The private log: attempts, their verifications, claims, self-labels and
    diagnoses, one append-only table each. A reader given a user reads that
    user's records alone, in the query."""

    def __init__(self, root: Database) -> None:
        self.root = root
        self._attempts = Log(root, attempts, Attempt)
        self._claims = Log(root, attempt_claims, AttemptClaim)
        self._self_labels = Log(root, self_labels, SelfLabel)
        self._diagnoses = Log(root, diagnoses, Diagnosis)

    def append_attempt(self, attempt: Attempt) -> None:
        with self.root.transaction():
            with self.root.begin() as conn:
                known(conn, attempt.user_id)
            self._attempts.append(attempt)

    def append_verification(self, verification: AttemptVerification) -> None:
        with self.root.begin() as conn:
            conn.execute(
                insert(attempt_verifications).values(verification.model_dump(exclude={"results"}))
            )
            if verification.results:
                conn.execute(
                    insert(attempt_verification_case_results),
                    [
                        one.model_dump()
                        | {"attempt_verification_id": verification.id, "position": position}
                        for position, one in enumerate(verification.results)
                    ],
                )

    def append_claim(self, claim: AttemptClaim) -> None:
        self._claims.append(claim)

    def append_self_label(self, label: SelfLabel) -> None:
        self._self_labels.append(label)

    def append_diagnosis(self, diagnosis: Diagnosis) -> None:
        self._diagnoses.append(diagnosis)

    def attempts(self, user_id: str | None = None) -> list[Attempt]:
        if user_id is None:
            return self._attempts.all()
        return self._attempts.where(attempts.c.user_id == user_id)

    def verifications(self, user_id: str | None = None) -> list[AttemptVerification]:
        with self.root.connect() as conn:
            runs = (
                conn.execute(
                    select(attempt_verifications)
                    .where(*theirs(attempt_verifications, user_id))
                    .order_by(attempt_verifications.c.appended)
                )
                .mappings()
                .all()
            )
            held = conn.execute(
                select(attempt_verification_case_results)
                .where(
                    attempt_verification_case_results.c.attempt_verification_id.in_(
                        [run["id"] for run in runs]
                    )
                )
                .order_by(attempt_verification_case_results.c.position)
            ).mappings()
            results: dict[str, list[dict[str, Any]]] = {run["id"]: [] for run in runs}
            for one in held:
                results[one["attempt_verification_id"]].append(dict(one))
        return [
            AttemptVerification.model_validate(dict(run) | {"results": results[run["id"]]})
            for run in runs
        ]

    def claims(self, user_id: str | None = None) -> list[AttemptClaim]:
        return self._claims.where(*theirs(attempt_claims, user_id))

    def self_labels(self, user_id: str | None = None) -> list[SelfLabel]:
        return self._self_labels.where(*theirs(self_labels, user_id))

    def diagnoses(self, user_id: str | None = None) -> list[Diagnosis]:
        return self._diagnoses.where(*theirs(diagnoses, user_id))


def theirs(table: Table, user_id: str | None) -> list[ColumnElement[bool]]:
    """The rows of a table keyed to an attempt that are the user's, or every
    row where no user is named."""
    if user_id is None:
        return []
    return [table.c.attempt_id.in_(select(attempts.c.id).where(attempts.c.user_id == user_id))]
