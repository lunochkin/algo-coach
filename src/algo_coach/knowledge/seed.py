"""Seeding a module: `knowledge.md`, Seeding."""

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import ColumnElement, Connection, Table, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from algo_coach.ids import new_id
from algo_coach.knowledge.check import COLUMNS, refusals
from algo_coach.knowledge.diagrams import (
    Drawer,
    DrawError,
    MermaidCli,
    mermaid_sources,
    store,
    undrawn,
)
from algo_coach.knowledge.files import ModuleSource
from algo_coach.knowledge.table import lessons, modules, questions, subtopics, topics
from algo_coach.schema import Module, Question
from algo_coach.storage import Database


class ModuleSeedResult(BaseModel):
    topics: int = 0
    subtopics: int = 0
    questions: int = 0
    lessons: int = 0
    diagrams: int = 0  # drawn by this seed, the rest drawn before
    retired: int = 0
    refused: list[str] = []


def seed_module(
    source: ModuleSource, *, root: Database, drawer: Drawer | None = None
) -> ModuleSeedResult:
    """Checks the module whole, draws each Mermaid source not yet drawn, then
    refreshes every row by slug, minting ids for the new ones and retiring the
    ones the files no longer hold."""
    if found := refusals(source):
        return ModuleSeedResult(refused=found)
    sources = mermaid_sources(source)
    tool, todo, drawn = "", list[str](), list[tuple[str, str]]()
    if sources:
        drawer = drawer or MermaidCli()
        # drawn before the transaction, since a draw takes about a second
        try:
            tool = drawer.version()
            with root.connect() as conn:
                todo = undrawn(conn, sources, tool)
            drawn = drawer.draw(todo) if todo else []
        except DrawError as error:
            return ModuleSeedResult(refused=[f"diagrams: {error}"])
    result = ModuleSeedResult(diagrams=len(todo))
    with root.begin() as conn:
        store(conn, todo, drawn, tool)
        of_module = select(questions.c.slug, questions.c.retired_at).join(modules)
        retired = {
            row.slug
            for row in conn.execute(of_module.where(modules.c.slug == source.slug))
            if row.retired_at is not None
        }
        reused = [
            f"{raw['id']}: a retired slug is never reused"
            for bank in source.banks
            for raw in bank.questions
            if raw["id"] in retired
        ]
        if reused:
            return ModuleSeedResult(refused=reused)
        module_id = _module(conn, source)
        subs = _topics(conn, source, module_id, result)
        result.questions = _questions(conn, source, module_id, subs, result)
        result.lessons = _lessons(conn, source, module_id, result)
    return result


def _module(conn: Connection, source: ModuleSource) -> str:
    course = source.course
    graph = {key: value for key, value in (source.graph or {}).items() if key != "lesson"}
    found = conn.execute(select(modules.c.id).where(modules.c.slug == source.slug)).scalar()
    module = Module.model_validate(
        {
            "id": found or new_id(),
            "slug": source.slug,
            "title": course["title"],
            "position": course.get("order", 100),
            "pass_ratio": course["pass_ratio"],
            "kinds": course["kinds"],
            "code_kinds": course.get("code_kinds", []),
            "code_lang": course.get("code_lang"),
            "graph": graph or None,
            "certifications": source.certifications,
        }
    )
    return _stored(conn, modules, found, module)


def _topics(
    conn: Connection, source: ModuleSource, module_id: str, result: ModuleSeedResult
) -> dict[str, str]:
    """Writes the topics and their subtopics, and returns each subtopic's id by
    its slug."""
    held = {row["slug"]: row for row in _rows(conn, topics, topics.c.module_id == module_id)}
    stored = {row["id"]: row for row in held.values()}
    listed = sorted(source.course.get("topic", []), key=lambda one: one["tier"])
    rows: list[dict[str, Any]] = []
    for position, topic in enumerate(listed):
        found = held.pop(topic["slug"], None)
        rows.append(
            {
                "id": found["id"] if found else new_id(),
                "module_id": module_id,
                "slug": topic["slug"],
                "retired_at": None,
                "title": topic["title"],
                "tier": topic["tier"],
                "position": position,
            }
        )
    _write(conn, topics, rows, stored)
    ids = [row["id"] for row in rows]
    held_subs = {
        (row["topic_id"], row["slug"]): row
        for row in _rows(conn, subtopics, subtopics.c.topic_id.in_(ids))
    }
    stored_subs = {row["id"]: row for row in held_subs.values()}
    subs: dict[str, str] = {}
    sub_rows: list[dict[str, Any]] = []
    for topic, topic_id in zip(listed, ids, strict=True):
        titles = topic.get("sub_titles", {})
        for at, slug in enumerate(topic["subs"]):
            found = held_subs.pop((topic_id, slug), None)
            subs[slug] = found["id"] if found else new_id()
            sub_rows.append(
                {
                    "id": subs[slug],
                    "topic_id": topic_id,
                    "slug": slug,
                    "retired_at": None,
                    "position": at,
                    "title": titles.get(slug),
                }
            )
        result.subtopics += len(topic["subs"])
    _write(conn, subtopics, sub_rows, stored_subs)
    result.retired += _retire(conn, subtopics, [row["id"] for row in held_subs.values()])
    result.topics = len(listed)
    result.retired += _retire(conn, topics, [row["id"] for row in held.values()])
    return subs


def _questions(
    conn: Connection,
    source: ModuleSource,
    module_id: str,
    subs: dict[str, str],
    result: ModuleSeedResult,
) -> int:
    within = questions.c.module_id == module_id
    held = {row["slug"]: row for row in _rows(conn, questions, within)}
    stored = {row["id"]: row for row in held.values()}
    rows: list[dict[str, Any]] = []
    for bank in source.banks:
        for position, raw in enumerate(bank.questions):
            form = raw.get("format", "choice")
            found = held.pop(raw["id"], None)
            # validated, so the JSONB columns hold what passed the model
            question = Question.model_validate(
                {
                    "id": found["id"] if found else new_id(),
                    "module_id": module_id,
                    "subtopic_id": subs[bank.sub],
                    "slug": raw["id"],
                    "position": position,
                    "level": raw["level"],
                    "kind": raw["kind"],
                    # `card` collides with a Card here: the glossary's `open`
                    "format": "open" if form == "card" else form,
                    "prompt": raw["prompt"],
                    "code": raw.get("code"),
                    "lesson": raw.get("lesson"),
                    "body": {key: value for key, value in raw.items() if key not in COLUMNS},
                }
            )
            rows.append(question.model_dump())
    _write(conn, questions, rows, stored)
    result.retired += _retire(conn, questions, [row["id"] for row in held.values()])
    return len(rows)


def _lessons(
    conn: Connection, source: ModuleSource, module_id: str, result: ModuleSeedResult
) -> int:
    within = lessons.c.module_id == module_id
    held = {row["slug"]: row for row in _rows(conn, lessons, within)}
    stored = {row["id"]: row for row in held.values()}
    authored: dict[str, dict[str, Any]] = (source.graph or {}).get("lesson", {})
    rows: list[dict[str, Any]] = []
    for slug, lesson in authored.items():
        found = held.pop(slug, None)
        rows.append(
            {
                "id": found["id"] if found else new_id(),
                "module_id": module_id,
                "slug": slug,
                "retired_at": None,
                "title": lesson["title"],
                "text": source.lesson_texts[slug],
                "minutes": lesson.get("minutes"),
                "pretest": lesson.get("pretest", 2),
                "teaches": lesson.get("teaches", []),
                "needs": lesson.get("needs", []),
            }
        )
    _write(conn, lessons, rows, stored)
    result.retired += _retire(conn, lessons, [row["id"] for row in held.values()])
    return len(authored)


def _rows(conn: Connection, table: Table, condition: ColumnElement[bool]) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(select(table).where(condition)).mappings()]


def _write(
    conn: Connection, table: Table, rows: list[dict[str, Any]], stored: dict[str, dict[str, Any]]
) -> None:
    """The rows that are new or differ from what is stored, in one statement.
    Through a tunnel each statement waits a round trip, so none is sent per
    row, and a row already stored as authored is not sent at all."""
    changed = [
        row
        for row in rows
        if (held := stored.get(row["id"])) is None
        or any(held.get(name) != value for name, value in row.items())
    ]
    if not changed:
        return
    statement = pg_insert(table)
    columns = [name for name in changed[0] if name != "id"]
    conn.execute(
        statement.on_conflict_do_update(
            index_elements=["id"], set_={name: statement.excluded[name] for name in columns}
        ),
        changed,
    )


def _stored(conn: Connection, table: Table, found: str | None, record: Module) -> str:
    """A validated record, so the JSONB columns hold what passed the model."""
    if found is None:
        conn.execute(insert(table).values(record.model_dump()))
    else:
        conn.execute(
            update(table).where(table.c.id == found).values(record.model_dump(exclude={"id"}))
        )
    return record.id


def _retire(conn: Connection, table: Table, held: Iterable[str]) -> int:
    ids = list(held)
    if not ids:
        return 0
    live = table.c.id.in_(ids) & table.c.retired_at.is_(None)
    return conn.execute(update(table).where(live).values(retired_at=datetime.now(UTC))).rowcount
