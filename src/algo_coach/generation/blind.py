"""The reference solution: the statement in, a solution out, and nothing else.

Blind is the whole point. Shown the canonical or its cases, the reference
inherits that solution's reading of the statement, and agreement then shows
only that one model is consistent with itself. Shown nothing but the prose,
agreement is evidence that the prose has one reading, and a disagreement on
any case discards the problem.

Its own brief for the same reason: the technique, the template and the cue are
what the statement is written to withhold, so none of them may appear here.
"""

from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Transport, ask
from algo_coach.generation.generator import DEFAULT, Configuration, GenerationError
from algo_coach.schema import Call

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
    """What the reference call returns: one solution and nothing about it.

    No cases, since the ones it would write would be its own reading of the
    statement rather than a test of it. No commentary, since nothing reads it.
    """

    solution: str = Field(min_length=1)


def prompt(statement: str) -> str:
    """The statement alone, delimited: it is data the model solves rather than
    instructions it follows."""
    return f"<problem>\n{statement}\n</problem>"


def read(text: str) -> str:
    """The solution, checked again on arrival as the draft is."""
    return Blind.model_validate_json(text).solution


def schema() -> dict[str, Any]:
    """One string, required. An object rather than bare text, so the code
    arrives as a value instead of inside whatever fences a model likes."""
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
    configuration: Configuration = DEFAULT,
) -> tuple[str, Call]:
    """One solution written from the statement, and the call that wrote it.

    The same configuration as the generation call by default. Independence is
    what the model was shown, not which model it was: a second model reading
    the canonical would inherit its reading all the same, and one model reading
    only the prose does not.
    """
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
