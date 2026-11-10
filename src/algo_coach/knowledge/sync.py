"""The app's sync: its records appended by `client_id`, and the user's records
since a cursor read back. `knowledge.md`, The records."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ValidationError
from sqlalchemy import Connection, Table, select
from sqlalchemy.dialects.postgresql import insert

from algo_coach.ids import new_id
from algo_coach.knowledge.table import (
    answers,
    certification_exams,
    focuses,
    lesson_marks,
    lessons,
    module_status_changes,
    modules,
    questions,
    stints,
    subtopics,
    topics,
)
from algo_coach.knowledge.wire import (
    Unknown,
    answer_out,
    certification_in,
    certification_out,
    mode_in,
    mode_out,
)
from algo_coach.schema import (
    Answer,
    CertificationExam,
    Focus,
    KnowledgeRecord,
    LessonMark,
    ModuleStatusChange,
    Stint,
)
from algo_coach.storage import Database

# learn's line kind, the table its record is stored in, and the record
KINDS: dict[str, tuple[Table, type[KnowledgeRecord]]] = {
    "attempt": (answers, Answer),
    "session": (stints, Stint),
    "status": (module_status_changes, ModuleStatusChange),
    "focus": (focuses, Focus),
    "lesson": (lesson_marks, LessonMark),
    "cert": (certification_exams, CertificationExam),
}


class Refusal(BaseModel):
    client_id: str
    reason: str


class Synced(BaseModel):
    stored: int = 0
    known: int = 0  # already stored under its `client_id`: a retried upload
    refused: list[Refusal] = []
    records: list[dict[str, Any]] = []
    cursor: dict[str, int] = {}  # each table's last append order this user read


def sync(
    root: Database, user_id: str, device: str, sent: list[dict[str, Any]], since: dict[str, int]
) -> Synced:
    result = Synced()
    with root.begin() as conn:
        names = _Names(conn)
        for line in sent:
            client_id = str(line.get("client_id") or "")
            try:
                table, values = _record(names, line)
                record = KINDS[line["kind"]][1](
                    id=new_id(), client_id=client_id, user_id=user_id, device=device,
                    at=line["t"], created_at=datetime.now(UTC), **values,
                )  # fmt: skip
            except (Unknown, ValidationError, KeyError, ValueError) as error:
                result.refused.append(Refusal(client_id=client_id, reason=_reason(error)))
                continue
            added = conn.execute(
                insert(table)
                .values(record.model_dump())
                .on_conflict_do_nothing(index_elements=["user_id", "client_id"])
                .returning(table.c.id)
            ).first()
            if added is None:
                result.known += 1
            else:
                result.stored += 1
        for kind, (table, _) in KINDS.items():
            rows = _since(conn, table, user_id, since.get(table.name, 0))
            result.records += [_line(kind, row, names) for row in rows]
            appended = [row["appended"] for row in rows] or [since.get(table.name, 0)]
            result.cursor[table.name] = max(appended)
    return result


class _Names:
    """Every slug against its minted id, both ways, read once per sync."""

    def __init__(self, conn: Connection) -> None:
        self.modules = {
            row.slug: row.id for row in conn.execute(select(modules.c.slug, modules.c.id))
        }
        self.slug = {id_: slug for slug, id_ in self.modules.items()}
        self.topics: dict[tuple[str, str], str] = {}
        self.subtopics: dict[tuple[str, str], str] = {}
        self.questions: dict[tuple[str, str], str] = {}
        self.lessons: dict[tuple[str, str], str] = {}
        self.owned: dict[str, tuple[str, str]] = {}  # a question's or lesson's module and slug
        for row in conn.execute(select(topics.c.module_id, topics.c.slug, topics.c.id)):
            self.topics[(row.module_id, row.slug)] = row.id
            self.slug[row.id] = row.slug
        nested = select(topics.c.module_id, subtopics.c.slug, subtopics.c.id).join(topics)
        for row in conn.execute(nested):
            self.subtopics[(row.module_id, row.slug)] = row.id
            self.slug[row.id] = row.slug
        for table, held in ((questions, self.questions), (lessons, self.lessons)):
            for row in conn.execute(select(table.c.module_id, table.c.slug, table.c.id)):
                held[(row.module_id, row.slug)] = row.id
                self.owned[row.id] = (self.slug[row.module_id], row.slug)

    def module(self, slug: str) -> str:
        if slug not in self.modules:
            raise Unknown(f"unknown module {slug}")
        return self.modules[slug]


def _record(names: _Names, line: dict[str, Any]) -> tuple[Table, dict[str, Any]]:
    kind = line["kind"]
    if kind not in KINDS:
        raise Unknown(f"unknown kind {kind}")
    table = KINDS[kind][0]
    if kind == "session":
        mode, level = mode_in(line["mode"])
        return table, {"mode": mode, "level": level, "score": line["score"], "answered": line["n"]}
    if kind == "focus":
        return table, _focus(names, line)
    module = line["course"]
    module_id = names.module(module)
    if kind == "attempt":
        question = names.questions.get((module_id, line["id"]))
        if question is None:
            raise Unknown(f"unknown question {module}/{line['id']}")
        ticks = {
            key: line[key] for key in ("guess", "grade", "missed", "traps", "wrong") if key in line
        }
        return table, {"question_id": question, "correct": line["ok"], **ticks}
    if kind == "status":
        return table, {"module_id": module_id, "status": line["status"]}
    if kind == "lesson":
        lesson = names.lessons.get((module_id, line["lesson"]))
        if lesson is None:
            raise Unknown(f"unknown lesson {module}/{line['lesson']}")
        return table, {"lesson_id": lesson, "read": line["status"] == "done"}
    topic, level = certification_in(module, line["cert"])
    return table, {
        "module_id": module_id,
        "topic_id": _topic(names, module_id, topic),
        "level": level,
        "score": line["score"],
        "answered": line["n"],
        "passed": line["passed"],
    }


def _focus(names: _Names, line: dict[str, Any]) -> dict[str, Any]:
    """Degrades as `knowledge.md` gives: an unknown topic keeps the module, and
    an unknown subtopic keeps the topic."""
    if line.get("course") is None:
        return {"strict": bool(line.get("strict"))}
    module_id = names.module(line["course"])
    topic = names.topics.get((module_id, line.get("topic") or ""))
    sub = names.subtopics.get((module_id, line.get("sub") or "")) if topic else None
    values: dict[str, Any] = {"module_id": module_id, "topic_id": topic, "subtopic_id": sub}
    if certification := line.get("cert"):
        scope, level = certification_in(line["course"], certification)
        values |= {"topic_id": _topic(names, module_id, scope), "subtopic_id": None}
        values["certification_level"] = level
    return values | {"strict": bool(line.get("strict"))}


def _topic(names: _Names, module_id: str, slug: str | None) -> str | None:
    if slug is None:
        return None
    if (module_id, slug) not in names.topics:
        raise Unknown(f"unknown topic {slug}")
    return names.topics[(module_id, slug)]


def _since(conn: Connection, table: Table, user_id: str, after: int) -> list[dict[str, Any]]:
    query = select(table).where(table.c.user_id == user_id, table.c.appended > after)
    return [dict(row) for row in conn.execute(query.order_by(table.c.appended)).mappings()]


def _line(kind: str, row: dict[str, Any], names: _Names) -> dict[str, Any]:
    line = {"kind": kind, "client_id": row["client_id"], "device": row["device"]}
    line["t"] = row["at"].isoformat()
    if kind == "attempt":
        module, question = names.owned[row["question_id"]]
        return line | answer_out({**row, "module": module, "question": question})
    if kind == "session":
        mode = mode_out(row["mode"], row["level"])
        return line | {"mode": mode, "score": row["score"], "n": row["answered"]}
    if kind == "lesson":
        module, lesson = names.owned[row["lesson_id"]]
        status = "done" if row["read"] else "undone"
        return line | {"course": module, "lesson": lesson, "status": status}
    module = names.slug.get(row.get("module_id") or "")
    topic = names.slug.get(row.get("topic_id") or "")
    if kind == "status":
        return line | {"course": module, "status": row["status"]}
    if kind == "focus":
        sub = names.slug.get(row["subtopic_id"] or "")
        line |= {"course": module, "topic": topic, "sub": sub, "strict": row["strict"]}
        if row["certification_level"] is not None:
            line["cert"] = certification_out(module or "", topic, row["certification_level"])
        return line
    certification = certification_out(module or "", topic, row["level"])
    return (
        line
        | {"course": module, "cert": certification, "score": row["score"]}
        | {
            "n": row["answered"],
            "passed": row["passed"],
        }
    )


def _reason(error: Exception) -> str:
    if isinstance(error, ValidationError):
        return "; ".join(
            f"{'.'.join(map(str, one['loc']))}: {one['msg']}" for one in error.errors()
        )
    if isinstance(error, KeyError):
        return f"missing {error.args[0]}"
    return str(error)
