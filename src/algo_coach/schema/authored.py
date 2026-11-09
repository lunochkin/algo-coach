"""The authored structure a content row holds as JSONB, typed so the seed
refuses a malformed one: `README.md`, Storage. The messages are learn's, as
`learn check` worded them."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

LETTERS = "ABCDEFGH"
RANKS = (0, 1, 2, 3)
RANK_NAMES = ("foundation", "associate", "professional", "expert")

Text = Annotated[str, StringConstraints(strip_whitespace=False, min_length=1, pattern=r"\S")]


class Authored(BaseModel):
    # a field the format does not know is a typo the seed would store unread
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Detail(Authored):
    """How a question's answer works, shown on request after an answer."""

    mechanism: Text
    example: Text | None = None
    pitfalls: list[Text] | None = Field(default=None, min_length=1, max_length=4)
    versions: Text | None = None
    diagram: Text | None = None


class ChoiceBody(Authored):
    choices: list[str]
    answer: list[str]  # letters into `choices`, more than one for a multi-select
    why: list[str]  # one line per choice, in the same order
    explain: str
    detail: Detail

    @model_validator(mode="after")
    def _choices_and_their_answer(self) -> ChoiceBody:
        n = len(self.choices)
        if not 3 <= n <= len(LETTERS):
            raise ValueError(f"{n} choices")
        if len(self.why) != n:
            raise ValueError(f"{len(self.why)} why for {n} choices")
        answer = self.answer
        if (
            not answer
            or len(set(answer)) != len(answer)
            or any(a not in LETTERS[:n] for a in answer)
        ):
            raise ValueError(f"bad answer {answer!r}")
        return self


class ShortBody(Authored):
    accept: list[str]  # the first is canonical
    case: bool = False
    explain: str
    detail: Detail

    @model_validator(mode="after")
    def _something_accepted(self) -> ShortBody:
        if not self.accept:
            raise ValueError("empty accept")
        return self


class OpenBody(Authored):
    """learn's `card`: the points the answer has to contain, and the traps."""

    key: list[Text]
    traps: list[Text] = Field(default_factory=list[str])
    explain: str | None = None
    detail: Detail | None = None
    key_detail: list[Text] | None = None
    traps_detail: list[Text] | None = None

    @model_validator(mode="after")
    def _points_and_their_details(self) -> OpenBody:
        if not 2 <= len(self.key) <= 6:
            raise ValueError("key must be a list of 2-6 non-empty points")
        if len(self.traps) > 3:
            raise ValueError("traps must be a list of 0-3 non-empty strings")
        for name, details, parent in (
            ("key_detail", self.key_detail, self.key),
            ("traps_detail", self.traps_detail, self.traps),
        ):
            if details is None:
                continue
            if len(details) != len(parent):
                raise ValueError(f"{name} must have one non-empty string per item ({len(parent)})")
            if any(len(one.strip().splitlines()) > 3 for one in details):
                raise ValueError(f"{name} items must be at most 3 lines")
        return self


type Body = ChoiceBody | ShortBody | OpenBody


class Edge(Authored):
    needs: str = Field(alias="from")  # the subtopic that needs
    to: str
    offset: int = Field(default=0, ge=0)


class GraphSettings(Authored):
    """A module's prerequisite graph. Its lessons are rows of their own."""

    format: Literal[1, 2] = 1
    match_up_to: int = Field(default=1, ge=0, le=3)
    needs: dict[str, list[str]] = Field(default_factory=dict[str, list[str]])
    edge: list[Edge] = Field(default_factory=list[Edge])

    def edges(self) -> list[tuple[str, str, int]]:
        return [(f, to, 0) for f, tos in self.needs.items() for to in tos] + [
            (one.needs, one.to, one.offset) for one in self.edge
        ]


class Exam(Authored):
    size: int | None = Field(default=None, ge=1)
    share: float | None = Field(default=None, alias="pass", gt=0, le=1)


class Retention(Authored):
    stability_days: float | None = Field(default=None, gt=0)
    share: float | None = Field(default=None, gt=0, le=1)


class CertificationRule(Authored):
    """Every field optional: a scope's rule overrides only what it names."""

    exam: Exam | None = None
    retention: Retention | None = None
    coverage_ratio: float | None = Field(default=None, gt=0, le=1)
    levels: list[Literal[0, 1, 2, 3]] | None = None
    min_pool_ratio: float | None = Field(default=None, ge=0)
    require_exam: bool | None = None
    lapse: bool | None = None


class ScopeRule(CertificationRule):
    """A scope's rule, and its rule per rank, named as learn named ranks."""

    foundation: CertificationRule | None = None
    associate: CertificationRule | None = None
    professional: CertificationRule | None = None
    expert: CertificationRule | None = None


class CertificationEdge(Authored):
    needs: str = Field(alias="from")
    to: str


class CertificationSettings(Authored):
    format: Literal[1] = 1
    defaults: CertificationRule = Field(default_factory=CertificationRule)
    scope: dict[str, ScopeRule] = Field(default_factory=dict[str, ScopeRule])
    edge: list[CertificationEdge] = Field(default_factory=list[CertificationEdge])
    unedge: list[CertificationEdge] = Field(default_factory=list[CertificationEdge])
