from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Double,
    ForeignKey,
    Integer,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from algo_coach.schema import ModuleStatus, OpenGrade, QuestionFormat, StintMode
from algo_coach.storage import appended_column, enumerated, metadata, timestamp

# a slug as `Slug` spells it
SLUG = "'^[a-z0-9][a-z0-9-]*$'"
RANK = "BETWEEN 0 AND 3"


# content: refreshed by the seed, matched by slug, retired rather than deleted
# once the log references a row: `knowledge.md`, Seeding

modules = Table(
    "modules",
    metadata,
    Column("id", Text, primary_key=True),
    Column("slug", Text, nullable=False, unique=True),
    Column("retired_at", timestamp()),
    Column("title", Text, nullable=False),
    Column("position", Integer, nullable=False),
    Column("pass_ratio", Double, nullable=False),
    Column("kinds", ARRAY(Text), nullable=False),
    Column("code_kinds", ARRAY(Text), nullable=False),
    Column("code_lang", Text),
    Column("graph", JSONB),
    Column("certifications", JSONB),
    CheckConstraint(f"slug ~ {SLUG}", name="slug_spelled"),
    CheckConstraint("pass_ratio > 0 AND pass_ratio <= 1", name="pass_ratio_a_share"),
)

topics = Table(
    "topics",
    metadata,
    Column("id", Text, primary_key=True),
    Column("module_id", Text, ForeignKey("modules.id"), nullable=False),
    Column("slug", Text, nullable=False),
    Column("retired_at", timestamp()),
    Column("title", Text, nullable=False),
    Column("tier", Integer, nullable=False),
    Column("position", Integer, nullable=False),
    UniqueConstraint("module_id", "slug"),
    CheckConstraint(f"slug ~ {SLUG}", name="slug_spelled"),
)

subtopics = Table(
    "subtopics",
    metadata,
    Column("id", Text, primary_key=True),
    Column("topic_id", Text, ForeignKey("topics.id"), nullable=False),
    Column("slug", Text, nullable=False),
    Column("retired_at", timestamp()),
    Column("position", Integer, nullable=False),
    Column("title", Text),
    UniqueConstraint("topic_id", "slug"),
    CheckConstraint(f"slug ~ {SLUG}", name="slug_spelled"),
)

questions = Table(
    "questions",
    metadata,
    Column("id", Text, primary_key=True),
    Column("module_id", Text, ForeignKey("modules.id"), nullable=False),
    Column("subtopic_id", Text, ForeignKey("subtopics.id"), nullable=False, index=True),
    Column("slug", Text, nullable=False),
    Column("retired_at", timestamp()),
    Column("position", Integer, nullable=False),
    Column("rank", Integer, nullable=False),
    Column("kind", Text, nullable=False),
    Column("format", enumerated(QuestionFormat), nullable=False),
    Column("prompt", Text, nullable=False),
    Column("code", Text),
    Column("lesson", Text),
    Column("body", JSONB, nullable=False),
    # a slug names one question for good, retired or not
    UniqueConstraint("module_id", "slug"),
    CheckConstraint(f"slug ~ {SLUG}", name="slug_spelled"),
    CheckConstraint(f"rank {RANK}", name="rank_ranked"),
    CheckConstraint("prompt <> ''", name="prompt_written"),
)

lessons = Table(
    "lessons",
    metadata,
    Column("id", Text, primary_key=True),
    Column("module_id", Text, ForeignKey("modules.id"), nullable=False),
    Column("slug", Text, nullable=False),
    Column("retired_at", timestamp()),
    Column("title", Text, nullable=False),
    Column("text", Text, nullable=False),
    Column("minutes", Integer),
    Column("pretest", Integer, nullable=False),
    Column("teaches", ARRAY(Text), nullable=False),
    Column("needs", ARRAY(Text), nullable=False),
    UniqueConstraint("module_id", "slug"),
    CheckConstraint(f"slug ~ {SLUG}", name="slug_spelled"),
    CheckConstraint("pretest BETWEEN 0 AND 5", name="pretest_bounded"),
    CheckConstraint("minutes >= 1", name="minutes_counted"),
)


# the knowledge log: append-only, each record minted by the client too, so a
# retried upload writes nothing twice: `knowledge.md`, The records
def _logged(name: str, *columns: Column[Any] | CheckConstraint) -> Table:
    return Table(
        name,
        metadata,
        Column("id", Text, primary_key=True),
        appended_column(),
        Column("client_id", Text, nullable=False),
        Column("user_id", Text, ForeignKey("users.id"), nullable=False, index=True),
        Column("device", Text, nullable=False),
        Column("at", timestamp(), nullable=False),
        Column("created_at", timestamp(), nullable=False),
        *columns,
        UniqueConstraint("user_id", "client_id"),
        CheckConstraint("client_id <> '' AND device <> ''", name="client_named"),
    )


answers = _logged(
    "answers",
    Column("question_id", Text, ForeignKey("questions.id"), nullable=False, index=True),
    Column("correct", Boolean, nullable=False),
    Column("guess", Boolean, nullable=False),
    Column("grade", enumerated(OpenGrade)),
    Column("missed", ARRAY(Integer), nullable=False),
    Column("traps", ARRAY(Integer), nullable=False),
    Column("wrong", Boolean, nullable=False),
    CheckConstraint(
        "grade IS NOT NULL OR (missed = '{}' AND traps = '{}' AND NOT wrong)",
        name="ticks_belong_to_a_grade",
    ),
    CheckConstraint("grade IS NULL OR NOT guess", name="an_open_question_takes_no_guess"),
)

stints = _logged(
    "stints",
    Column("mode", enumerated(StintMode), nullable=False),
    Column("rank", Integer),
    Column("score", Integer, nullable=False),
    Column("answered", Integer, nullable=False),
    CheckConstraint("(mode = 'exam') = (rank IS NOT NULL)", name="an_exam_names_its_rank"),
    CheckConstraint(f"rank {RANK}", name="rank_ranked"),
    CheckConstraint("score BETWEEN 0 AND answered", name="scored"),
)

module_status_changes = _logged(
    "module_status_changes",
    Column("module_id", Text, ForeignKey("modules.id"), nullable=False),
    Column("status", enumerated(ModuleStatus), nullable=False),
)

focuses = _logged(
    "focuses",
    Column("module_id", Text, ForeignKey("modules.id")),
    Column("topic_id", Text, ForeignKey("topics.id")),
    Column("subtopic_id", Text, ForeignKey("subtopics.id")),
    Column("certification_rank", Integer),
    Column("strict", Boolean, nullable=False),
    CheckConstraint("topic_id IS NULL OR module_id IS NOT NULL", name="topic_within_module"),
    CheckConstraint("subtopic_id IS NULL OR topic_id IS NOT NULL", name="subtopic_within_topic"),
    CheckConstraint(
        "certification_rank IS NULL OR (module_id IS NOT NULL AND subtopic_id IS NULL)",
        name="certification_a_module_or_topic",
    ),
    CheckConstraint(f"certification_rank {RANK}", name="rank_ranked"),
)

lesson_marks = _logged(
    "lesson_marks",
    Column("lesson_id", Text, ForeignKey("lessons.id"), nullable=False),
    Column("read", Boolean, nullable=False),
)

certification_exams = _logged(
    "certification_exams",
    Column("module_id", Text, ForeignKey("modules.id"), nullable=False),
    Column("topic_id", Text, ForeignKey("topics.id")),
    Column("rank", Integer, nullable=False),
    Column("score", Integer, nullable=False),
    Column("answered", Integer, nullable=False),
    Column("passed", Boolean, nullable=False),
    CheckConstraint(f"rank {RANK}", name="rank_ranked"),
    CheckConstraint("score BETWEEN 0 AND answered", name="scored"),
)
