"""What decides whether a solution to a generated problem is correct.

Written with the problem, in the same call as the statement. Cases derived
afterwards describe whatever the solution happens to do, where cases written
with the statement describe what the problem asks. Nothing in this model can
enforce that: it is a property of the act that writes them, and the generate
command is what holds it.

Carries no provenance of its own. A case is not a reading, and the problem it
is keyed to already names the configuration that wrote both.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


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
