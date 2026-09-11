"""One user's whole log, read out and erased as one: `log.md` gives what it
holds, and why no other user's record is touched."""

from pydantic import BaseModel
from sqlalchemy import Connection, delete, select, text

from algo_coach.calls.table import calls
from algo_coach.log.sittings import SittingStore
from algo_coach.log.store import AttemptLog
from algo_coach.log.table import (
    attempt_claims,
    attempt_verification_case_results,
    attempt_verifications,
    attempts,
    diagnoses,
    self_labels,
    sitting_pauses,
    sittings,
)
from algo_coach.schema import (
    Attempt,
    AttemptClaim,
    AttemptVerification,
    Call,
    Diagnosis,
    SelfLabel,
    Sitting,
)
from algo_coach.storage import Database


class UserLog(BaseModel):
    """Every record of one user's log, and the calls a model made about the
    user's code."""

    user_id: str
    sittings: list[Sitting]
    attempts: list[Attempt]
    verifications: list[AttemptVerification]
    claims: list[AttemptClaim]
    self_labels: list[SelfLabel]
    diagnoses: list[Diagnosis]
    calls: list[Call]


def whole_log(root: Database, user_id: str) -> UserLog:
    log = AttemptLog(root)
    claims = log.claims(user_id)
    diagnosed = log.diagnoses(user_id)
    named = {one.call_id for one in [*claims, *diagnosed] if one.call_id is not None}
    with root.connect() as conn:
        rows = conn.execute(
            select(calls).where(calls.c.id.in_(named)).order_by(calls.c.appended)
        ).mappings()
        called = [Call.model_validate(dict(row)) for row in rows]
    return UserLog(
        user_id=user_id,
        sittings=SittingStore(root).all(user_id),
        attempts=log.attempts(user_id),
        verifications=log.verifications(user_id),
        claims=claims,
        self_labels=log.self_labels(user_id),
        diagnoses=diagnosed,
        calls=called,
    )


def erased(root: Database, user_id: str) -> dict[str, int]:
    """Deletes the user's whole log in one transaction, and each call a model
    made about the user's code that no other record names. Returns how many
    rows left each table."""
    theirs = select(attempts.c.id).where(attempts.c.user_id == user_id)
    runs = select(attempt_verifications.c.id).where(attempt_verifications.c.attempt_id.in_(theirs))
    held = select(sittings.c.id).where(sittings.c.user_id == user_id)
    counted: dict[str, int] = {}
    with root.begin() as conn:
        # the one delete the append-only tables let through, and for this
        # transaction alone
        conn.execute(text("SET LOCAL algo_coach.erasing = 'on'"))
        named = set(
            conn.execute(
                select(attempt_claims.c.call_id).where(
                    attempt_claims.c.attempt_id.in_(theirs), attempt_claims.c.call_id.is_not(None)
                )
            ).scalars()
        ) | set(
            conn.execute(
                select(diagnoses.c.call_id).where(diagnoses.c.attempt_id.in_(theirs))
            ).scalars()
        )
        # children before the rows they name, since the foreign keys refuse the
        # other order
        for table, where in (
            (
                attempt_verification_case_results,
                attempt_verification_case_results.c.attempt_verification_id.in_(runs),
            ),
            (attempt_verifications, attempt_verifications.c.attempt_id.in_(theirs)),
            (attempt_claims, attempt_claims.c.attempt_id.in_(theirs)),
            (self_labels, self_labels.c.attempt_id.in_(theirs)),
            (diagnoses, diagnoses.c.attempt_id.in_(theirs)),
            (attempts, attempts.c.user_id == user_id),
            (sitting_pauses, sitting_pauses.c.sitting_id.in_(held)),
            (sittings, sittings.c.user_id == user_id),
        ):
            counted[table.name] = conn.execute(delete(table).where(where)).rowcount
        counted["calls"] = _unnamed_calls(conn, named)
    return counted


def _unnamed_calls(conn: Connection, named: set[str]) -> int:
    # every column the database knows to reference a call, read from its
    # catalog, so a table added later keeps its calls without an edit here
    referencing = conn.execute(
        text(
            "SELECT conrelid::regclass::text, attname FROM pg_constraint"
            " JOIN pg_attribute ON attrelid = conrelid AND attnum = ANY(conkey)"
            " WHERE contype = 'f' AND confrelid = 'calls'::regclass"
        )
    ).all()
    still = " AND ".join(
        f'NOT EXISTS (SELECT 1 FROM "{table}" WHERE "{column}" = calls.id)'
        for table, column in referencing
    )
    return conn.execute(
        text(f"DELETE FROM calls WHERE id = ANY(:named) AND {still}"), {"named": sorted(named)}
    ).rowcount
