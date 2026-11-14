from collections.abc import Sequence
from typing import Any

from sqlalchemy import ColumnElement, RowMapping, delete, insert, select
from sqlalchemy.dialects.postgresql import insert as upsert

from algo_coach.drafts.table import (
    SettledField,
    draft_declared_cases,
    draft_settled_cases,
    drafts,
)
from algo_coach.schema import CallSite, Draft, MachineProvenance, SettledCase
from algo_coach.storage import Database, called, configurations, configured

LISTS = {"declared", "cases", "kept", "won", "separating_case"}
SITES = {f"{site}_provenance" for site in CallSite}


class DraftStore:
    """Working state rather than a log: a draft is revised as each step
    answers, and removed once the problem it became has landed."""

    def __init__(self, root: Database) -> None:
        self.root = root

    def put(self, record: Draft) -> None:
        provenances = [getattr(record, name) for name in SITES]
        settled = {name: _settled(record, name) for name in SettledField}
        row = record.model_dump(exclude=LISTS | SITES) | {
            f"{site}_call_id": _call_id(getattr(record, f"{site}_provenance")) for site in CallSite
        }
        with self.root.begin() as conn:
            called(
                conn,
                [one for one in provenances if one is not None]
                + [case.provenance for cases in settled.values() for case in cases],
            )
            conn.execute(
                upsert(drafts).values(row).on_conflict_do_update(index_elements=["id"], set_=row)
            )
            # simple rather than a diff: every case the draft holds is written
            # again, and the draft store is working state a later refactor may
            # revise
            for child in (draft_declared_cases, draft_settled_cases):
                conn.execute(delete(child).where(child.c.draft_id == record.id))
            if record.declared:
                conn.execute(
                    insert(draft_declared_cases),
                    [
                        one.model_dump() | {"draft_id": record.id, "position": position}
                        for position, one in enumerate(record.declared)
                    ],
                )
            rows = [
                case.model_dump(exclude={"provenance"})
                | {
                    "draft_id": record.id,
                    "draft_field": field,
                    "position": position,
                    "call_id": case.provenance.call_id,
                }
                for field, cases in settled.items()
                for position, case in enumerate(cases)
            ]
            if rows:
                conn.execute(insert(draft_settled_cases), rows)

    def get(self, id: str) -> Draft | None:
        found = self._read(drafts.c.id == id)
        return found[0] if found else None

    def all(self) -> list[Draft]:
        return self._read()

    def remove(self, draft_id: str) -> None:
        # what clearing at landing does, the draft's cases with it. Missing is
        # not an error: a run that died between landing and clearing leaves the
        # next one this to do
        with self.root.begin() as conn:
            conn.execute(delete(drafts).where(drafts.c.id == draft_id))

    def _read(self, *where: ColumnElement[bool]) -> list[Draft]:
        with self.root.connect() as conn:
            rows = [
                dict(one)
                for one in conn.execute(
                    select(drafts).where(*where).order_by(drafts.c.id)
                ).mappings()
            ]
            ids = [one["id"] for one in rows]
            declared = (
                conn.execute(
                    select(draft_declared_cases)
                    .where(draft_declared_cases.c.draft_id.in_(ids))
                    .order_by(draft_declared_cases.c.position)
                )
                .mappings()
                .all()
            )
            settled = (
                conn.execute(
                    select(draft_settled_cases)
                    .where(draft_settled_cases.c.draft_id.in_(ids))
                    .order_by(draft_settled_cases.c.position)
                )
                .mappings()
                .all()
            )
            calls = {one["call_id"] for one in settled} | {
                one[f"{site}_call_id"] for one in rows for site in CallSite
            }
            known = configurations(conn, calls - {None})
        return [_draft(row, declared, settled, known) for row in rows]


def _settled(record: Draft, field: str) -> list[SettledCase]:
    held: list[SettledCase] | SettledCase | None = getattr(record, field)
    if held is None:
        return []
    return held if isinstance(held, list) else [held]


def _call_id(provenance: MachineProvenance | None) -> str | None:
    return None if provenance is None else provenance.call_id


def _draft(
    row: dict[str, Any],
    declared: Sequence[RowMapping],
    settled: Sequence[RowMapping],
    known: dict[str, dict[str, Any]],
) -> Draft:
    fields = {name: value for name, value in row.items() if not name.endswith("_call_id")}
    for site in CallSite:
        call_id = row[f"{site}_call_id"]
        fields[f"{site}_provenance"] = (
            None if call_id is None else configured({"call_id": call_id}, known)
        )
    fields["declared"] = [
        {"args": one["args"], "expected": one["expected"]}
        for one in declared
        if one["draft_id"] == row["id"]
    ]
    for field in SettledField:
        cases = [
            {name: one[name] for name in ("args", "expected", "expected_from", "round", "repeats")}
            | {"provenance": configured({"call_id": one["call_id"]}, known)}
            for one in settled
            if one["draft_id"] == row["id"] and one["draft_field"] == field
        ]
        fields[field] = (cases[0] if cases else None) if field == "separating_case" else cases
    return Draft.model_validate(fields)
