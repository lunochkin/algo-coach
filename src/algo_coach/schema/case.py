"""What decides whether a solution to a generated problem is correct.

Written with the problem, in the same call as the statement. Cases derived
afterwards describe whatever the solution happens to do, where cases written
with the statement describe what the problem asks. Nothing in this model can
enforce that: it is a property of the act that writes them, and the generate
command is what holds it.

Carries no provenance of its own. A case is not a reading, and the problem it
is keyed to already names the configuration that wrote both.
"""

from collections.abc import Iterable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ExpectedSource(StrEnum):
    """Which solution computed a case's expected output.

    Not `SolutionRole` under another name: it answers how strong the case is
    rather than what a solution displays. The reference is different code from
    a call that saw the statement alone, so a case it computed is a test. One
    only the canonical could compute passes by construction, and is evidence
    about the cap rather than about the verdict. A third arm — two canonicals
    of different forms agreeing at scale — is additive if it is ever wanted.
    """

    REFERENCE = "reference"
    CANONICAL = "canonical"


class TestCase(BaseModel):
    """One call of a solution, and what it must return.

    Owned by the product, so the rule against third-party test cases in git
    binds nothing a generated problem ships.
    """

    id: str  # engine-minted, as every reference in the log is
    # the problem these cases decide. A case has no meaning apart from one,
    # and nothing shares a case between problems
    problem_id: str = Field(min_length=1)
    # the arguments, positionally. Empty is legal: a problem may ask for a
    # function of no arguments, and a case that passes none still decides one
    args: list[Any] = Field(default_factory=list)
    # what the solution must return. Required rather than defaulted, since a
    # case without one decides nothing; `None` is a value a solution may
    # legitimately return, which is why absence cannot stand in for it
    expected: Any
    # which solution computed `expected`. Required rather than defaulted: two
    # cases in a set are not equally strong, and a model default would answer
    # for a writer that never asked the question. `mint.case` carries the rule
    expected_from: ExpectedSource


class CaseOutcome(StrEnum):
    """How one case went. The kinds are apart because a failure mode reads
    them apart: only one of the three is evidence of slowness."""

    PASSED = "passed"
    # returned something other than the expected value
    WRONG = "wrong"
    # exceeded the wall-clock cap, which is what a case sized to force one
    # is written to do
    TIMEOUT = "timeout"
    # raised rather than returning
    CRASHED = "crashed"


class CaseResult(BaseModel):
    """One case, run against one solution.

    Per case rather than a share, and carrying the outcome rather than a
    verdict. A share cannot say which input timed out, and a set of the cases
    that passed cannot say why the rest did not.
    """

    case_id: str = Field(min_length=1)
    outcome: CaseOutcome
    # what the child measured around `solve`. The separating input a speedup
    # search looks for is found from these numbers, and a result holding only
    # the outcome would make every search re-run the whole set. Absent where
    # the child measured nothing: code defining no `solve` never reaches one,
    # and a timeout the parent's own timer decided was reported by nothing
    elapsed_ms: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _a_case_that_yielded_a_value_was_timed(self) -> CaseResult:
        """`PASSED` and `WRONG` come from a child that ran `solve` to
        completion, so the measurement exists. Stored without it, the case
        would be invisible to a search the run already paid for."""
        if self.outcome in (CaseOutcome.PASSED, CaseOutcome.WRONG) and self.elapsed_ms is None:
            raise ValueError(f"a {self.outcome} case carries the elapsed_ms the child measured")
        return self


def severest(outcomes: Iterable[CaseOutcome]) -> CaseOutcome | None:
    """How a set of cases went as a whole.

    The most severe failure stands. A solution that only ran slowly is
    otherwise correct, and that is a different remedy from one returning a
    wrong answer.

    `None` where no case was run. An empty set would otherwise fold to passed
    and claim a run that never happened.
    """
    seen = list(outcomes)
    if not seen:
        return None
    for outcome in (CaseOutcome.CRASHED, CaseOutcome.WRONG, CaseOutcome.TIMEOUT):
        if outcome in seen:
            return outcome
    return CaseOutcome.PASSED
