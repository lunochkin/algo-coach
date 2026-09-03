"""The reference solution: the statement in, a solution out, and nothing else.

Its own brief, naming no technique, template or cue: those are what the
statement withholds.
"""

from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Configuration, Transport, ask
from algo_coach.generation.errors import GenerationError
from algo_coach.schema import Call

# unmeasured, as every site's is. Greedy: this site writes against a statement
# that already exists, so its variance buys no diversity
BLIND_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio", temperature=0.0
)

SYSTEM = """You write a correct solution to a problem statement.

The statement is all you are given. Write the plainest solution that is
certainly correct: what the prose says, done directly. Do not optimise, and do
not reach for a technique the statement did not ask for.

Follow the statement literally. Where it leaves something undecided, implement
what it says rather than what you take it to have meant. Another solution is
being written from the same prose, and where the two disagree the problem is
discarded rather than either solution corrected.

Python, one module-level function named `solve`, taking its arguments
positionally in the order the statement describes them. The code stands
alone: no input is read and nothing is printed."""


class Blind(BaseModel):
    # no cases: the ones it would write are its own reading of the statement
    # rather than a test of it
    solution: str = Field(min_length=1)


def prompt(statement: str) -> str:
    # delimited: the statement is data the model solves, not instructions
    return f"<problem>\n{statement}\n</problem>"


def read(text: str) -> str:
    return Blind.model_validate_json(text).solution


def schema() -> dict[str, Any]:
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


def reference(
    transport: Transport,
    log: CallLog,
    statement: str,
    *,
    configuration: Configuration = BLIND_DEFAULT,
) -> tuple[str, Call]:
    # the site's own configuration by default: independence is what the model
    # was shown, so this call may run the model that wrote the statement
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
        raise GenerationError(call.error or "no solution")
    return read(text), call


__all__ = ["SYSTEM", "Blind", "prompt", "read", "reference", "schema"]
