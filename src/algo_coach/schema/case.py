"""What decides whether a solution to a generated problem is correct.

Written with the problem, in the same call as the statement. Cases derived
afterwards describe whatever the solution happens to do, where cases written
with the statement describe what the problem asks. Nothing in this model can
enforce that: it is a property of the act that writes them, and the generate
command is what holds it.

Carries no provenance of its own. A case is not a reading, and the problem it
is keyed to already names the configuration that wrote both.
"""

from typing import Any

from pydantic import BaseModel, Field


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
