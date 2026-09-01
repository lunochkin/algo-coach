from enum import StrEnum

from pydantic import Field, model_validator

from algo_coach.schema.provenance import MachineProvenance


class ProblemDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ProblemStatus(StrEnum):
    """Where a problem is in its life, apart from why it got there."""

    # written and verified, not yet cleared to serve
    CREATED = "created"
    # served by the drill loop
    ACTIVE = "active"
    # no longer served. `retired_reason` says why, and readers branch on that
    RETIRED = "retired"


class RetirementReason(StrEnum):
    """Why a problem stopped being served. Named rather than flagged, because
    the two are read differently once the board counts anything."""

    # the statement asked for something its cases do not decide. The failure
    # was the problem's, so its attempts are excluded from mastery
    DEFECTIVE = "defective"
    # the statement names its own approach, which the announcement floor
    # rejects. It asked what its cases decide, so its attempts are kept
    TELEGRAPHED = "telegraphed"


class Problem(MachineProvenance):
    id: str  # engine-minted, as every reference in the log is
    title: str
    # derived from the problem's canonical solutions, so re-derivable at any
    # time: a canonical added later can widen them
    techniques: list[str] = Field(default_factory=list)
    difficulty: ProblemDifficulty | None = None
    # what the problem asks; matching reads it, and a problem without one can
    # never be matched
    statement: str = Field(min_length=1)
    # the template it was written for, where the brief named one. An assertion
    # rather than a reading, which is what makes the first `TemplateMatch`
    # provenance. It never claims the problem exercises nothing else, which is
    # the matcher's question.
    #
    # Absent on a problem written from a technique brief: nothing told the
    # generator a form, so nothing may assert a pair. A technique brief asserts
    # no technique either — what such a problem is about comes from the
    # readings of its canonicals, as it does for every other problem
    generated_for: str | None = Field(default=None, min_length=1)
    # where the problem is in its life. Separate from the reason, since
    # `CREATED` and `ACTIVE` have none and only one transition needs one
    status: ProblemStatus = ProblemStatus.CREATED
    # why it stopped being served, absent unless it did. A field rather than a
    # record of its own, unlike a self-label or a claim: those are split
    # because two writers answer the same question and one has to stand over
    # the other, where nothing but the user ever retires a problem
    retired_reason: RetirementReason | None = None

    @model_validator(mode="after")
    def _provenance_required(self) -> Problem:
        self.check_provenance(True)
        return self

    @model_validator(mode="after")
    def _retirement_names_its_reason(self) -> Problem:
        """The status and the reason cannot disagree. A retired problem whose
        reason went missing would be excluded or counted by whichever reader
        guessed, and a reason on a served problem names a retirement that did
        not happen."""
        retired = self.status is ProblemStatus.RETIRED
        if retired and self.retired_reason is None:
            raise ValueError("a retired problem names its retired_reason")
        if not retired and self.retired_reason is not None:
            raise ValueError(f"a {self.status} problem carries no retired_reason")
        return self
