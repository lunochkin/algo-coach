"""What every solution this engine runs must be, stated once.

Four briefs ask for code, and each stated the same three facts in its own
words. `corpus.md` gives the entry point as an invariant, so a per-brief copy
of it is a copy that can drift.

Each brief still writes its own signature: the two that answer a statement take
what the prose describes, and the input generator takes a size and a seed.
"""

from typing import Any

from pydantic import BaseModel, Field

# named because the runner executes under it: a model writing for an older
# interpreter reaches stdlib behaviour this one rejects
RUNTIME = "Python 3.14"

ENTRY = "one module-level function named `solve`"

ALONE = "The code stands alone: no input is read and nothing is printed."

# corpus.md, "The statement carries the signature, and the order is why"
SIGNATURE = "a `def solve(...)` line naming the parameters in the order the cases pass them"

POSITIONAL = (
    "taking its arguments positionally, in the order the statement's `def solve(...)` line gives"
)


class Solved(BaseModel):
    """A brief's reply carrying one solution and nothing else. No cases: the
    ones it would write are its own reading of the statement rather than a
    test of it."""

    solution: str = Field(min_length=1)


def read_solution(text: str) -> str:
    return Solved.model_validate_json(text).solution


def solution_schema() -> dict[str, Any]:
    # an object rather than bare text, so the code arrives as a value instead
    # of inside whatever fences a model likes
    return {
        "type": "object",
        "properties": {
            "solution": {"type": "string", "description": "Python defining `solve`"},
        },
        "required": ["solution"],
        "additionalProperties": False,
    }


__all__ = [
    "ALONE",
    "ENTRY",
    "POSITIONAL",
    "RUNTIME",
    "SIGNATURE",
    "Solved",
    "read_solution",
    "solution_schema",
]
