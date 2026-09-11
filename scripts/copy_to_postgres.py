"""Copy every record under `data/` into the Postgres DATABASE_URL names, then
read each one back and compare it with the record it was copied from.

One-off: the stores still write JSON. Refuses a database whose tables already
hold rows, and writes everything in one transaction or nothing.

    uv run python scripts/copy_to_postgres.py
"""

import importlib
import os
import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel
from sqlalchemy import Connection, Table, create_engine, func, insert, select

import algo_coach
from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cases import CaseLog
from algo_coach.drafts import DraftStore
from algo_coach.log import AttemptLog, SittingStore
from algo_coach.matches import MatchLog
from algo_coach.outcomes import OutcomeLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Attempt,
    AttemptClaim,
    AttemptVerification,
    Call,
    CallSite,
    Card,
    Diagnosis,
    Draft,
    MachineProvenance,
    Problem,
    SelfLabel,
    SiteOutcome,
    Sitting,
    Solution,
    SolutionClaim,
    TemplateMatch,
    TestCase,
    Verification,
)
from algo_coach.solution_claims import SolutionClaimLog
from algo_coach.solutions import SolutionLog
from algo_coach.storage import metadata
from algo_coach.verifications import VerificationLog

ROOT = Path("data")
CONFIGURATION = [name for name in MachineProvenance.model_fields if name != "call_id"]
SETTLED = ("cases", "kept", "won", "separating_case")

source = Path(algo_coach.__file__).parent
for path in sorted(source.rglob("table.py")):
    importlib.import_module(
        ".".join(("algo_coach", *path.relative_to(source).with_suffix("").parts))
    )
T = metadata.tables


def row(record: BaseModel, table: Table, **extra: object) -> dict[str, Any]:
    """The record's values for the table's columns: a nested record as prefixed
    columns, and nothing the table has no column for."""
    values = dict(record.model_dump(mode="python"))
    flat: dict[str, Any] = {}
    for name, value in values.items():
        if isinstance(value, dict) and f"{name}_" in " ".join(
            column.name for column in table.columns
        ):
            flat |= {f"{name}_{inner}": one for inner, one in value.items()}
        else:
            flat[name] = value
    flat |= extra
    # every column on every row: a multi-row insert takes its columns from the
    # first row, and drops what a later row carries beyond them
    # not the append order, which the database numbers as the rows land
    return {
        column.name: flat.get(column.name) for column in table.columns if column.identity is None
    }


def rows_of(stores: dict[str, list[BaseModel]]) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def children(
        table: str, parent: str, parent_id: str, items: Iterable[BaseModel], **extra: object
    ) -> None:
        for position, item in enumerate(items):
            rows[table].append(
                row(item, T[table], **{parent: parent_id, "position": position}, **extra)
            )

    seen_users: dict[str, datetime] = {}
    for one in stores["attempts"] + stores["sittings"]:
        dumped = one.model_dump()
        at = dumped.get("started_at") or dumped["finished_at"]
        seen_users[one.user_id] = min(seen_users.get(one.user_id, at), at)
    rows["users"] = [{"id": user, "created_at": at} for user, at in seen_users.items()]

    for name in (
        "calls",
        "problems",
        "test_cases",
        "solutions",
        "solution_claims",
        "template_matches",
        "site_outcomes",
        "attempts",
        "attempt_claims",
        "self_labels",
        "diagnoses",
    ):
        rows[name] = [row(one, T[name]) for one in stores[name]]
    for card in stores["cards"]:
        rows["cards"].append(row(card, T["cards"]))
        children("card_templates", "card_id", card.id, card.templates)
    for run in stores["verifications"]:
        rows["verifications"].append(row(run, T["verifications"]))
        children("verification_case_results", "verification_id", run.id, run.results)
    for run in stores["attempt_verifications"]:
        rows["attempt_verifications"].append(row(run, T["attempt_verifications"]))
        children(
            "attempt_verification_case_results", "attempt_verification_id", run.id, run.results
        )
    for sitting in stores["sittings"]:
        rows["sittings"].append(row(sitting, T["sittings"]))
        children("sitting_pauses", "sitting_id", sitting.id, sitting.pauses)
    for draft in stores["drafts"]:
        calls = {
            f"{site}_call_id": getattr(draft, f"{site}_provenance").call_id
            for site in CallSite
            if getattr(draft, f"{site}_provenance") is not None
        }
        rows["drafts"].append(row(draft, T["drafts"], **calls))
        children("draft_declared_cases", "draft_id", draft.id, draft.declared)
        for field in SETTLED:
            held = getattr(draft, field)
            listed = [] if held is None else held if isinstance(held, list) else [held]
            for position, case in enumerate(listed):
                rows["draft_settled_cases"].append(
                    row(
                        case,
                        T["draft_settled_cases"],
                        draft_id=draft.id,
                        draft_field=field,
                        position=position,
                        call_id=case.provenance.call_id,
                    )
                )
    return rows


def loaded() -> dict[str, list[BaseModel]]:
    log = AttemptLog(ROOT)
    return {
        "calls": CallLog(ROOT).all(),
        "cards": CardStore(ROOT).all(),
        "problems": ProblemStore(ROOT).all(),
        "test_cases": CaseLog(ROOT).all(),
        "solutions": SolutionLog(ROOT).solutions(),
        "solution_claims": SolutionClaimLog(ROOT).claims(),
        "template_matches": MatchLog(ROOT).matches(),
        "verifications": VerificationLog(ROOT).all(),
        "site_outcomes": OutcomeLog(ROOT).all(),
        "drafts": DraftStore(ROOT).all(),
        "sittings": SittingStore(ROOT).all(),
        "attempts": log.attempts(),
        "attempt_verifications": log.verifications(),
        "attempt_claims": log.claims(),
        "self_labels": log.self_labels(),
        "diagnoses": log.diagnoses(),
    }


# ---- reading back


def read(conn: Connection, name: str) -> list[dict[str, Any]]:
    table = T[name]
    order = [table.c[key] for key in ("position",) if key in table.c]
    return [dict(one) for one in conn.execute(select(table).order_by(*order)).mappings()]


def grouped(rows: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for one in rows:
        found[one[key]].append(one)
    return found


def without(one: dict[str, Any], *names: str) -> dict[str, Any]:
    return {key: value for key, value in one.items() if key not in names}


def rebuilt(conn: Connection) -> dict[str, list[BaseModel]]:
    calls = {one["id"]: one for one in read(conn, "calls")}

    def configured(one: dict[str, Any]) -> dict[str, Any]:
        call = calls.get(one.get("call_id"))
        return one | {name: (call[name] if call else None) for name in CONFIGURATION}

    def plain(name: str, model: type[BaseModel], machine: bool = False) -> list[BaseModel]:
        return [
            model.model_validate(configured(one) if machine else one) for one in read(conn, name)
        ]

    templates = grouped(read(conn, "card_templates"), "card_id")
    cards = [
        Card.model_validate(
            {k: v for k, v in one.items() if not k.startswith("selector_")}
            | {
                "selector": {
                    "technique": one["selector_technique"],
                    "difficulty": one["selector_difficulty"],
                    "size": one["selector_size"],
                }
            }
            | {"templates": [without(t, "card_id", "position") for t in templates[one["id"]]]}
        )
        for one in read(conn, "cards")
    ]
    results = grouped(read(conn, "verification_case_results"), "verification_id")
    runs = [
        Verification.model_validate(
            one
            | {"results": [without(r, "verification_id", "position") for r in results[one["id"]]]}
        )
        for one in read(conn, "verifications")
    ]
    attempt_results = grouped(
        read(conn, "attempt_verification_case_results"), "attempt_verification_id"
    )
    attempt_runs = [
        AttemptVerification.model_validate(
            one
            | {
                "results": [
                    without(r, "attempt_verification_id", "position")
                    for r in attempt_results[one["id"]]
                ]
            }
        )
        for one in read(conn, "attempt_verifications")
    ]
    pauses = grouped(read(conn, "sitting_pauses"), "sitting_id")
    sittings = [
        Sitting.model_validate(
            one | {"pauses": [without(p, "sitting_id", "position") for p in pauses[one["id"]]]}
        )
        for one in read(conn, "sittings")
    ]

    declared = grouped(read(conn, "draft_declared_cases"), "draft_id")
    settled = grouped(read(conn, "draft_settled_cases"), "draft_id")
    drafts = []
    for one in read(conn, "drafts"):
        fields = {k: v for k, v in one.items() if not k.endswith("_call_id")}
        for site in CallSite:
            call_id = one[f"{site}_call_id"]
            fields[f"{site}_provenance"] = (
                None if call_id is None else configured({"call_id": call_id})
            )
        fields["declared"] = [without(c, "draft_id", "position") for c in declared[one["id"]]]
        cases = [c for c in settled[one["id"]]]
        for field in SETTLED:
            listed = [
                without(c, "draft_id", "draft_field", "position", "call_id")
                | {"provenance": configured({"call_id": c["call_id"]})}
                for c in sorted(
                    (c for c in cases if c["draft_field"] == field), key=lambda c: c["position"]
                )
            ]
            fields[field] = (
                (listed[0] if listed else None) if field == "separating_case" else listed
            )
        drafts.append(Draft.model_validate(fields))

    return {
        "calls": [Call.model_validate(one) for one in calls.values()],
        "cards": cards,
        "problems": plain("problems", Problem, machine=True),
        "test_cases": plain("test_cases", TestCase, machine=True),
        "solutions": plain("solutions", Solution, machine=True),
        "solution_claims": plain("solution_claims", SolutionClaim, machine=True),
        "template_matches": plain("template_matches", TemplateMatch, machine=True),
        "verifications": runs,
        "site_outcomes": plain("site_outcomes", SiteOutcome, machine=True),
        "drafts": drafts,
        "sittings": sittings,
        "attempts": plain("attempts", Attempt),
        "attempt_verifications": attempt_runs,
        "attempt_claims": plain("attempt_claims", AttemptClaim, machine=True),
        "self_labels": plain("self_labels", SelfLabel),
        "diagnoses": plain("diagnoses", Diagnosis, machine=True),
    }


def key(one: BaseModel) -> str:
    return str(one.model_dump()["id"])


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL names the database to copy into")
    engine = create_engine(url.replace("postgres://", "postgresql+psycopg://", 1))

    stores = loaded()
    rows = rows_of(stores)
    with engine.begin() as conn:
        held = {
            t.name: conn.execute(select(func.count()).select_from(t)).scalar_one()
            for t in metadata.sorted_tables
        }
        if any(held.values()):
            filled = ", ".join(f"{name} {count}" for name, count in held.items() if count)
            sys.exit(f"the tables already hold rows: {filled}")
        # parents before the rows that reference them
        for table in metadata.sorted_tables:
            if rows.get(table.name):
                conn.execute(insert(table), rows[table.name])
        for table in metadata.sorted_tables:
            print(f"{table.name:36} {len(rows.get(table.name, [])):>5}")

    with engine.connect() as conn:
        back = rebuilt(conn)
    different = 0
    for name, originals in stores.items():
        mine = sorted(originals, key=key)
        theirs = sorted(back[name], key=key)
        if len(mine) != len(theirs):
            print(f"{name}: {len(mine)} records, {len(theirs)} read back")
            different += 1
            continue
        for a, b in zip(mine, theirs, strict=True):
            if a != b:
                different += 1
                if different <= 10:
                    changed = [f for f in type(a).model_fields if getattr(a, f) != getattr(b, f)]
                    print(f"{name} {key(a)}: differs in {changed}")
    total = sum(len(v) for v in stores.values())
    print(f"\n{total} records copied; {total - different} read back equal, {different} differ")
    if different:
        sys.exit(1)


if __name__ == "__main__":
    main()
