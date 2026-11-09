"""the knowledge module

Revision: aeb1f4b74958
Revises: e39f193ac6d8
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "aeb1f4b74958"
down_revision: str | Sequence[str] | None = "e39f193ac6d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# named rather than declared, so a column referencing one creates none
MODULE_STATUS = postgresql.ENUM(
    "active", "paused", "archived", name="module_status", create_type=False
)
STINT_MODE = postgresql.ENUM(
    "next", "review", "filtered", "exam", name="stint_mode", create_type=False
)
QUESTION_FORMAT = postgresql.ENUM(
    "choice", "short", "open", name="question_format", create_type=False
)
OPEN_GRADE = postgresql.ENUM("k", "p", "n", name="open_grade", create_type=False)
ENUMS = (MODULE_STATUS, STINT_MODE, QUESTION_FORMAT, OPEN_GRADE)

# the user's knowledge log: `knowledge.md`, The records
APPEND_ONLY = (
    "answers",
    "stints",
    "module_status_changes",
    "focuses",
    "lesson_marks",
    "certification_exams",
)


def upgrade() -> None:
    # created once, before the tables using them: a column declaring its own
    # type would create it a second time
    for kind in ENUMS:
        postgresql.ENUM(*kind.enums, name=kind.name).create(op.get_bind())

    op.create_table(
        "modules",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("pass_ratio", sa.Double(), nullable=False),
        sa.Column("kinds", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("code_kinds", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("code_lang", sa.Text(), nullable=True),
        sa.Column("graph", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("certifications", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9][a-z0-9-]*$'", name=op.f("modules_slug_spelled_check")
        ),
        sa.CheckConstraint(
            "pass_ratio > 0 AND pass_ratio <= 1", name=op.f("modules_pass_ratio_a_share_check")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("modules_pkey")),
        sa.UniqueConstraint("slug", name=op.f("modules_slug_key")),
    )
    op.create_table(
        "lessons",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=True),
        sa.Column("pretest", sa.Integer(), nullable=False),
        sa.Column("teaches", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("needs", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9][a-z0-9-]*$'", name=op.f("lessons_slug_spelled_check")
        ),
        sa.CheckConstraint("minutes >= 1", name=op.f("lessons_minutes_counted_check")),
        sa.CheckConstraint("pretest BETWEEN 0 AND 5", name=op.f("lessons_pretest_bounded_check")),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name=op.f("lessons_module_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("lessons_pkey")),
        sa.UniqueConstraint("module_id", "slug", name=op.f("lessons_module_id_slug_key")),
    )
    op.create_table(
        "module_status_changes",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("status", MODULE_STATUS, nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''",
            name=op.f("module_status_changes_client_named_check"),
        ),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], name=op.f("module_status_changes_module_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("module_status_changes_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("module_status_changes_pkey")),
        sa.UniqueConstraint("appended", name=op.f("module_status_changes_appended_key")),
        sa.UniqueConstraint(
            "user_id", "client_id", name=op.f("module_status_changes_user_id_client_id_key")
        ),
    )
    op.create_index(
        op.f("module_status_changes_user_id_idx"),
        "module_status_changes",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "stints",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mode", STINT_MODE, nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("answered", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "(mode = 'exam') = (rank IS NOT NULL)", name=op.f("stints_an_exam_names_its_rank_check")
        ),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("stints_client_named_check")
        ),
        sa.CheckConstraint("rank BETWEEN 0 AND 3", name=op.f("stints_rank_ranked_check")),
        sa.CheckConstraint("score BETWEEN 0 AND answered", name=op.f("stints_scored_check")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("stints_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("stints_pkey")),
        sa.UniqueConstraint("appended", name=op.f("stints_appended_key")),
        sa.UniqueConstraint("user_id", "client_id", name=op.f("stints_user_id_client_id_key")),
    )
    op.create_index(op.f("stints_user_id_idx"), "stints", ["user_id"], unique=False)
    op.create_table(
        "topics",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint("slug ~ '^[a-z0-9][a-z0-9-]*$'", name=op.f("topics_slug_spelled_check")),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name=op.f("topics_module_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("topics_pkey")),
        sa.UniqueConstraint("module_id", "slug", name=op.f("topics_module_id_slug_key")),
    )
    op.create_table(
        "certification_exams",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("answered", sa.Integer(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("certification_exams_client_named_check")
        ),
        sa.CheckConstraint(
            "rank BETWEEN 0 AND 3", name=op.f("certification_exams_rank_ranked_check")
        ),
        sa.CheckConstraint(
            "score BETWEEN 0 AND answered", name=op.f("certification_exams_scored_check")
        ),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], name=op.f("certification_exams_module_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], name=op.f("certification_exams_topic_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("certification_exams_user_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("certification_exams_pkey")),
        sa.UniqueConstraint("appended", name=op.f("certification_exams_appended_key")),
        sa.UniqueConstraint(
            "user_id", "client_id", name=op.f("certification_exams_user_id_client_id_key")
        ),
    )
    op.create_index(
        op.f("certification_exams_user_id_idx"), "certification_exams", ["user_id"], unique=False
    )
    op.create_table(
        "lesson_marks",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lesson_id", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("lesson_marks_client_named_check")
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lessons.id"], name=op.f("lesson_marks_lesson_id_fkey")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("lesson_marks_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("lesson_marks_pkey")),
        sa.UniqueConstraint("appended", name=op.f("lesson_marks_appended_key")),
        sa.UniqueConstraint(
            "user_id", "client_id", name=op.f("lesson_marks_user_id_client_id_key")
        ),
    )
    op.create_index(op.f("lesson_marks_user_id_idx"), "lesson_marks", ["user_id"], unique=False)
    op.create_table(
        "subtopics",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("topic_id", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9][a-z0-9-]*$'", name=op.f("subtopics_slug_spelled_check")
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name=op.f("subtopics_topic_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("subtopics_pkey")),
        sa.UniqueConstraint("topic_id", "slug", name=op.f("subtopics_topic_id_slug_key")),
    )
    op.create_table(
        "focuses",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=True),
        sa.Column("topic_id", sa.Text(), nullable=True),
        sa.Column("subtopic_id", sa.Text(), nullable=True),
        sa.Column("certification_rank", sa.Integer(), nullable=True),
        sa.Column("strict", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("focuses_client_named_check")
        ),
        sa.CheckConstraint(
            "certification_rank BETWEEN 0 AND 3", name=op.f("focuses_rank_ranked_check")
        ),
        sa.CheckConstraint(
            "certification_rank IS NULL OR (module_id IS NOT NULL AND subtopic_id IS NULL)",
            name=op.f("focuses_certification_a_module_or_topic_check"),
        ),
        sa.CheckConstraint(
            "subtopic_id IS NULL OR topic_id IS NOT NULL",
            name=op.f("focuses_subtopic_within_topic_check"),
        ),
        sa.CheckConstraint(
            "topic_id IS NULL OR module_id IS NOT NULL",
            name=op.f("focuses_topic_within_module_check"),
        ),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name=op.f("focuses_module_id_fkey")),
        sa.ForeignKeyConstraint(
            ["subtopic_id"], ["subtopics.id"], name=op.f("focuses_subtopic_id_fkey")
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], name=op.f("focuses_topic_id_fkey")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("focuses_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("focuses_pkey")),
        sa.UniqueConstraint("appended", name=op.f("focuses_appended_key")),
        sa.UniqueConstraint("user_id", "client_id", name=op.f("focuses_user_id_client_id_key")),
    )
    op.create_index(op.f("focuses_user_id_idx"), "focuses", ["user_id"], unique=False)
    op.create_table(
        "questions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("module_id", sa.Text(), nullable=False),
        sa.Column("subtopic_id", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("format", QUESTION_FORMAT, nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=True),
        sa.Column("lesson", sa.Text(), nullable=True),
        sa.Column("body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint("prompt <> ''", name=op.f("questions_prompt_written_check")),
        sa.CheckConstraint(
            "slug ~ '^[a-z0-9][a-z0-9-]*$'", name=op.f("questions_slug_spelled_check")
        ),
        sa.CheckConstraint("rank BETWEEN 0 AND 3", name=op.f("questions_rank_ranked_check")),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], name=op.f("questions_module_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["subtopic_id"], ["subtopics.id"], name=op.f("questions_subtopic_id_fkey")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("questions_pkey")),
        sa.UniqueConstraint("module_id", "slug", name=op.f("questions_module_id_slug_key")),
    )
    op.create_index(op.f("questions_subtopic_id_idx"), "questions", ["subtopic_id"], unique=False)
    op.create_table(
        "answers",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("appended", sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column("client_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("device", sa.Text(), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("question_id", sa.Text(), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("guess", sa.Boolean(), nullable=False),
        sa.Column("grade", OPEN_GRADE, nullable=True),
        sa.Column("missed", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("traps", postgresql.ARRAY(sa.Integer()), nullable=False),
        sa.Column("wrong", sa.Boolean(), nullable=False),
        sa.CheckConstraint(
            "client_id <> '' AND device <> ''", name=op.f("answers_client_named_check")
        ),
        sa.CheckConstraint(
            "grade IS NOT NULL OR (missed = '{}' AND traps = '{}' AND NOT wrong)",
            name=op.f("answers_ticks_belong_to_a_grade_check"),
        ),
        sa.CheckConstraint(
            "grade IS NULL OR NOT guess", name=op.f("answers_an_open_question_takes_no_guess_check")
        ),
        sa.ForeignKeyConstraint(
            ["question_id"], ["questions.id"], name=op.f("answers_question_id_fkey")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("answers_user_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("answers_pkey")),
        sa.UniqueConstraint("appended", name=op.f("answers_appended_key")),
        sa.UniqueConstraint("user_id", "client_id", name=op.f("answers_user_id_client_id_key")),
    )
    op.create_index(op.f("answers_question_id_idx"), "answers", ["question_id"], unique=False)
    op.create_index(op.f("answers_user_id_idx"), "answers", ["user_id"], unique=False)

    for table in APPEND_ONLY:
        op.execute(
            f"CREATE TRIGGER append_only BEFORE UPDATE OR DELETE ON {table}"
            " FOR EACH STATEMENT EXECUTE FUNCTION refuse_rewrite()"
        )


def downgrade() -> None:
    op.drop_index(op.f("answers_user_id_idx"), table_name="answers")
    op.drop_index(op.f("answers_question_id_idx"), table_name="answers")
    op.drop_table("answers")
    op.drop_index(op.f("questions_subtopic_id_idx"), table_name="questions")
    op.drop_table("questions")
    op.drop_index(op.f("focuses_user_id_idx"), table_name="focuses")
    op.drop_table("focuses")
    op.drop_table("subtopics")
    op.drop_index(op.f("lesson_marks_user_id_idx"), table_name="lesson_marks")
    op.drop_table("lesson_marks")
    op.drop_index(op.f("certification_exams_user_id_idx"), table_name="certification_exams")
    op.drop_table("certification_exams")
    op.drop_table("topics")
    op.drop_index(op.f("stints_user_id_idx"), table_name="stints")
    op.drop_table("stints")
    op.drop_index(op.f("module_status_changes_user_id_idx"), table_name="module_status_changes")
    op.drop_table("module_status_changes")
    op.drop_table("lessons")
    op.drop_table("modules")
    for kind in ENUMS:
        kind.drop(op.get_bind())
