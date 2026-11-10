"""The knowledge module's content and the knowledge log: `knowledge.md`."""

from datetime import datetime
from enum import StrEnum
from typing import Any, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)

from algo_coach.schema.authored import (
    Authored,
    Body,
    CertificationSettings,
    ChoiceBody,
    GraphSettings,
    OpenBody,
    ShortBody,
)
from algo_coach.schema.card import Slug

# 0 Foundation, 1 Associate, 2 Professional, 3 Expert
RANKS = range(4)


class QuestionFormat(StrEnum):
    CHOICE = "choice"
    SHORT = "short"
    OPEN = "open"


class OpenGrade(StrEnum):
    """An open question's grade, from the points ticked: `knowledge.md`."""

    KNOWN = "k"
    PARTIAL = "p"
    NONE = "n"


class StintMode(StrEnum):
    NEXT = "next"
    REVIEW = "review"
    FILTERED = "filtered"
    EXAM = "exam"


class ModuleStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Seeded(BaseModel):
    """What every content row carries: the minted id, the authored slug a
    re-seed matches on, and the retirement that replaces a delete."""

    id: str
    slug: Slug
    retired_at: datetime | None = None


class Module(Seeded):
    title: str = Field(min_length=1)
    position: int
    pass_ratio: float = Field(gt=0, le=1)
    kinds: list[str]
    code_kinds: list[str] = Field(default_factory=list[str])
    code_lang: str | None = None
    # content edited without a migration: `knowledge.md`, Gating
    graph: GraphSettings | None = None
    certifications: CertificationSettings | None = None

    @field_serializer("graph", "certifications")
    def _as_authored(self, value: Authored | None) -> dict[str, Any] | None:
        return _authored(value)


class Topic(Seeded):
    module_id: str
    title: str = Field(min_length=1)
    tier: int
    position: int


class Subtopic(Seeded):
    topic_id: str
    position: int
    title: str | None = None  # shown in place of the slug, where the topic gives one


class Question(Seeded):
    module_id: str
    subtopic_id: str
    position: int
    rank: int = Field(ge=0, le=3)
    kind: str = Field(min_length=1)
    format: QuestionFormat
    prompt: str = Field(min_length=1)
    code: str | None = None
    lesson: str | None = None  # a lesson slug, with `#anchor` naming a heading
    # the format's own fields and the detail, passed to the app as authored
    body: Body

    @field_validator("body", mode="before")
    @classmethod
    def _body_of_its_format(cls, value: object, info: ValidationInfo) -> object:
        form = info.data.get("format")
        if isinstance(value, dict) and isinstance(form, QuestionFormat):
            return BODIES[form].model_validate(cast(dict[str, Any], value))
        # anything else is the union's to refuse
        return cast(object, value)

    @field_serializer("body")
    def _body_as_authored(self, value: Authored) -> dict[str, Any] | None:
        return _authored(value)


BODIES: dict[QuestionFormat, type[Authored]] = {
    QuestionFormat.CHOICE: ChoiceBody,
    QuestionFormat.SHORT: ShortBody,
    QuestionFormat.OPEN: OpenBody,
}


def _authored(value: Authored | None) -> dict[str, Any] | None:
    # the fields the author wrote, under the names the author wrote them by
    return (
        None if value is None else value.model_dump(mode="json", by_alias=True, exclude_unset=True)
    )


class Lesson(Seeded):
    module_id: str
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    minutes: int | None = Field(default=None, ge=1)
    pretest: int = Field(default=2, ge=0, le=5)
    teaches: list[str] = Field(default_factory=list[str])
    needs: list[str] = Field(default_factory=list[str])


class KnowledgeRecord(BaseModel):
    """What every record of the knowledge log carries: `knowledge.md`, The
    records."""

    model_config = ConfigDict(frozen=True)

    id: str
    # minted by the client, so a retried upload writes nothing twice
    client_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    device: str = Field(min_length=1)
    at: datetime  # when the user acted, which the schedule reads
    created_at: datetime  # when the record reached the server


class Answer(KnowledgeRecord):
    question_id: str
    correct: bool
    guess: bool = False
    # an open question's alone, with the ticks it was graded from
    grade: OpenGrade | None = None
    missed: list[int] = Field(default_factory=list[int])
    traps: list[int] = Field(default_factory=list[int])
    wrong: bool = False

    @model_validator(mode="after")
    def _ticks_belong_to_a_grade(self) -> Answer:
        if self.grade is None and (self.missed or self.traps or self.wrong):
            raise ValueError("only an open question's answer carries ticks")
        if self.grade is not None and self.guess:
            raise ValueError("an open question takes no guess")
        return self


class Stint(KnowledgeRecord):
    mode: StintMode
    rank: int | None = Field(default=None, ge=0, le=3)  # an exam's alone
    score: int = Field(ge=0)  # the answers that were correct
    answered: int = Field(ge=0)

    @model_validator(mode="after")
    def _an_exam_names_its_rank(self) -> Stint:
        if (self.mode is StintMode.EXAM) != (self.rank is not None):
            raise ValueError("an exam names its rank, and no queue does")
        return self


class ModuleStatusChange(KnowledgeRecord):
    module_id: str
    status: ModuleStatus


class Focus(KnowledgeRecord):
    """No module clears the focus. A certification is its module, its topic
    or none for the whole module, and its rank."""

    module_id: str | None = None
    topic_id: str | None = None
    subtopic_id: str | None = None
    certification_rank: int | None = Field(default=None, ge=0, le=3)
    strict: bool = False

    @model_validator(mode="after")
    def _each_narrows_the_one_above(self) -> Focus:
        if self.topic_id is not None and self.module_id is None:
            raise ValueError("a topic is focused within its module")
        if self.subtopic_id is not None and self.topic_id is None:
            raise ValueError("a subtopic is focused within its topic")
        if self.certification_rank is not None and (
            self.module_id is None or self.subtopic_id is not None
        ):
            raise ValueError("a certification is a module or a topic at a rank")
        return self


class LessonMark(KnowledgeRecord):
    lesson_id: str
    read: bool  # false resets a lesson read before


class CertificationExam(KnowledgeRecord):
    module_id: str
    topic_id: str | None = None  # none for the whole module
    rank: int = Field(ge=0, le=3)
    score: int = Field(ge=0)  # the answers that were correct
    answered: int = Field(ge=0)
    passed: bool
