"""The naive solution: the approach the card's form replaces, which is what the
speedup search measures the canonical against.

It settles no case and discards no problem, so it is the one answering site
that may be told which form to avoid, and the one that is sampled. `corpus.md`
gives what it may never do.
"""

from typing import Any

from pydantic import BaseModel, Field

from algo_coach.calls import CallLog, Configuration, Transport, ask, prompt_hash
from algo_coach.generation.contract import ALONE, ENTRY, RUNTIME
from algo_coach.generation.errors import GenerationError
from algo_coach.schema import Call

# Sampled rather than greedy, as the generator is: it produces an artifact
# rather than a verdict, and a second call is a second draw where the first
# wrote the form.
CLOCK_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio"
)

SYSTEM = f"""You write the solution a solver reaches for without one technique.

You are told which approach to avoid. Write what someone who does not know it
writes: the statement's own definition, computed directly. Another solution
uses that approach, and what is measured is how much faster it is than yours.
Correctness is the only thing asked of you.

Compute the answer the way the statement defines it. Where it asks for the best
of something, check every candidate its definition admits and keep the best.

The candidates are what the statement's own bounds admit. Where the answer is a
number, try every value between the bounds the statement gives it. Do not
narrow that range to the values the input happens to contain, and do not skip a
value because an argument shows the answer cannot be there. Such an argument is
what the fast solution is built on, and using it here leaves nothing to
measure.

Do not search a space wider than the definition names. Trying every subset,
every ordering or every pairing where the statement describes a scan is slower
than the approach the technique replaces. A solution that slow is separated by
an input of a few dozen elements, and no submission is judged at that size.

Do not precompute, do not cache a result, do not reach for a data structure,
and do not stop a loop early. A loop that runs to the end is what is wanted.

Do not use the approach you are told to avoid, and do not use another approach
that reaches the same running time by a different route.

{RUNTIME}, {ENTRY}, taking its arguments
positionally in the order the statement describes them.
{ALONE}"""


class Naive(BaseModel):
    # no cases and no bound: it answers the problem's own cases, and how far it
    # can be pushed is what the search measures rather than what it declares
    solution: str = Field(min_length=1)


def prompt(statement: str, avoid: str) -> str:
    # delimited: both are data the model writes against, not instructions
    return f"<problem>\n{statement}\n</problem>\n\n<avoid>\n{avoid}\n</avoid>"


def read(text: str) -> str:
    return Naive.model_validate_json(text).solution


def request_hash(statement: str, avoid: str) -> str:
    return prompt_hash(SYSTEM, prompt(statement, avoid))


def schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "solution": {"type": "string", "description": "Python defining `solve`"},
        },
        "required": ["solution"],
        "additionalProperties": False,
    }


def naive(
    transport: Transport,
    log: CallLog,
    statement: str,
    avoid: str,
    *,
    configuration: Configuration = CLOCK_DEFAULT,
) -> tuple[str, Call]:
    # the form to avoid is the template's trigger, which no other site may be
    # shown: this one settles no case, so nothing it reads reaches a verdict
    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(statement, avoid),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(),
    )
    if text is None:
        raise GenerationError(call.error or "no solution")
    return read(text), call


__all__ = [
    "CLOCK_DEFAULT",
    "SYSTEM",
    "Naive",
    "naive",
    "prompt",
    "read",
    "request_hash",
    "schema",
]
