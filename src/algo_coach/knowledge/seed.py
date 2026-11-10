"""Seeding a module: `knowledge.md`, Seeding."""

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy import ColumnElement, Connection, Table, insert, select, update

from algo_coach.ids import new_id
from algo_coach.knowledge.check import COLUMNS, refusals
from algo_coach.knowledge.files import ModuleSource
from algo_coach.knowledge.table import lessons, modules, questions, subtopics, topics
from algo_coach.schema import Module, Question
from algo_coach.storage import Database


class ModuleSeedResult(BaseModel):
    topics: int = 0
    subtopics: int = 0
    questions: int = 0
    lessons: int = 0
    retired: int = 0
    refused: list[str] = []


def seed_module(source: ModuleSource, *, root: Database) -> ModuleSeedResult:
    """Checks the module whole, then refreshes every row by slug, minting ids
    for the new ones and retiring the ones the files no longer hold."""
    if found := refusals(source):
        return ModuleSeedResult(refused=found)
    result = ModuleSeedResult()
    with root.begin() as conn:
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
    held = {row["slug"]: row["id"] for row in _rows(conn, topics, topics.c.module_id == module_id)}
    subs: dict[str, str] = {}
    listed = sorted(source.course.get("topic", []), key=lambda one: one["tier"])
    for position, topic in enumerate(listed):
        values = {"module_id": module_id, "slug": topic["slug"], "retired_at": None}
        values |= {"title": topic["title"], "tier": topic["tier"], "position": position}
        topic_id = _put(conn, topics, held.pop(topic["slug"], None), values)
        within = subtopics.c.topic_id == topic_id
        held_subs = {row["slug"]: row["id"] for row in _rows(conn, subtopics, within)}
        titles = topic.get("sub_titles", {})
        for at, slug in enumerate(topic["subs"]):
            values = {"topic_id": topic_id, "slug": slug, "retired_at": None, "position": at}
            values["title"] = titles.get(slug)
            subs[slug] = _put(conn, subtopics, held_subs.pop(slug, None), values)
        result.subtopics += len(topic["subs"])
        result.retired += _retire(conn, subtopics, held_subs.values())
    result.topics = len(listed)
    result.retired += _retire(conn, topics, held.values())
    return subs


def _questions(
    conn: Connection,
    source: ModuleSource,
    module_id: str,
    subs: dict[str, str],
    result: ModuleSeedResult,
) -> int:
    within = questions.c.module_id == module_id
    held = {row["slug"]: row["id"] for row in _rows(conn, questions, within)}
    count = 0
    for bank in source.banks:
        for position, raw in enumerate(bank.questions):
            form = raw.get("format", "choice")
            found = held.pop(raw["id"], None)
            question = Question.model_validate(
                {
                    "id": found or new_id(),
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
            _stored(conn, questions, found, question)
            count += 1
    result.retired += _retire(conn, questions, held.values())
    return count


def _lessons(
    conn: Connection, source: ModuleSource, module_id: str, result: ModuleSeedResult
) -> int:
    within = lessons.c.module_id == module_id
    held = {row["slug"]: row["id"] for row in _rows(conn, lessons, within)}
    authored: dict[str, dict[str, Any]] = (source.graph or {}).get("lesson", {})
    for slug, lesson in authored.items():
        values = {
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
        _put(conn, lessons, held.pop(slug, None), values)
    result.retired += _retire(conn, lessons, held.values())
    return len(authored)


def _rows(conn: Connection, table: Table, condition: ColumnElement[bool]) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(select(table).where(condition)).mappings()]


def _put(conn: Connection, table: Table, found: str | None, values: dict[str, Any]) -> str:
    if found is None:
        found = new_id()
        conn.execute(insert(table).values(id=found, **values))
    else:
        conn.execute(update(table).where(table.c.id == found).values(**values))
    return found


def _stored(conn: Connection, table: Table, found: str | None, record: Module | Question) -> str:
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
