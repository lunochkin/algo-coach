"""The input generator: the statement in, code building an input of a given
size out.

What the speedup search runs to reach a size. Its own brief, naming no
technique and no form: the constraints are what it reads, and the statement is
where they are stated.
"""

from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport, ask
from algo_coach.generation.generator import DEFAULT, Configuration, GenerationError
from algo_coach.schema import Call

SYSTEM = """You write a program that builds an input for a problem statement.

The statement is all you are given. Write Python defining one module-level
function named `solve`, taking a single positional argument `size`. It returns
an array: the positional arguments of a case, in the order the statement
describes them. `solve` is the name every module this engine runs defines, and
says nothing about what yours computes.

`size` scales the input. What it counts is yours to choose where the statement
describes several inputs: the length of the collection, the number of rows,
whatever the work grows with. Size 1 is the smallest input the statement
admits.

The same size builds the same input every time. Seed any randomness from `size`
itself, so an input is reproducible from the size alone.

The input satisfies every constraint the statement gives, at every size. Values
stay inside the ranges it states, and the shape stays what it describes.

Report the largest size the statement allows, in the unit your `size` counts.
That bound is what stops a search asking for an input the problem excludes.

The code stands alone: no input is read and nothing is printed."""


class Built(BaseModel):
    """What one call returns: the generator, and how far it may be pushed."""

    code: str = Field(min_length=1)
    largest: int = Field(gt=0)


def prompt(statement: str) -> str:
    # delimited: the statement is data the model builds for, not instructions
    return f"<problem>\n{statement}\n</problem>"


def read(text: str) -> Built:
    return Built.model_validate_json(text)


def schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python defining `solve(size)`"},
            "largest": {
                "type": "integer",
                "description": "the largest size the statement's constraints allow",
            },
        },
        "required": ["code", "largest"],
        "additionalProperties": False,
    }


def builder(
    transport: Transport,
    log: CallLog,
    statement: str,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[Built, Call]:
    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(statement),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(),
    )
    if text is None:
        raise GenerationError(call.error or "no generator")
    return read(text), call


__all__ = ["SYSTEM", "Built", "builder", "prompt", "read", "schema"]
