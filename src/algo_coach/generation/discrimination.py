"""The call that answers a survivor: the arguments of a case that catches it.

Arguments alone. The reference computes what they return, so no model writes an
expected output that could agree with the mistake the case was asked for.
"""

import json
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field, field_validator

from algo_coach.calls import CallLog, Configuration, Transport, ask
from algo_coach.generation.errors import GenerationError
from algo_coach.mutation import Mutant
from algo_coach.schema import Call

# unmeasured, as every site's is. Greedy: this site writes against a statement
# that already exists, so its variance buys no diversity
DISCRIMINATION_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio", temperature=0.0
)

SYSTEM = """You write the inputs that catch a wrong solution.

You are given a problem statement, a correct solution to it, and mutants: copies
of that solution, each with one change. Every mutant passes every case the
problem has, so the case set does not catch the change.

Return the positional arguments of cases that would. A case catches a mutant
when the mutant and the correct solution return different values for those
arguments.

You write no expected value. An independent solution computes what a case
returns, and a value you wrote here could agree with the mutant you just read
rather than with the statement.

Every case satisfies the constraints the statement gives. An input the problem
excludes catches nothing, because no solution owes an answer on it.

Answer each mutant, and give several inputs where one does not separate a
change on its own. Prefer the smallest input that separates: a boundary, an
empty collection, a tie, a repeated element.

`args` is an array of the positional arguments, in the order `solve` takes them,
written as JSON inside a string."""


def prompt(
    statement: str,
    canonical: str,
    survivors: Sequence[Mutant],
    known: Sequence[Sequence[Any]] = (),
) -> str:
    return "\n".join(
        [
            f"<problem>\n{statement}\n</problem>",
            "",
            "<solution>",
            canonical,
            "</solution>",
            *already(known),
            "",
            *(line for mutant in survivors for line in shown(mutant)),
        ]
    )


def already(known: Sequence[Sequence[Any]]) -> list[str]:
    # what the set holds, so the reply proposes an input rather than one of
    # these. The expected values are left out: the solution above is what says
    # how the problem behaves
    if not known:
        return []
    return ["", "Cases the set already has:", *(f"  {json.dumps(list(one))}" for one in known)]


def shown(mutant: Mutant) -> list[str]:
    # the change beside the code: the reply is aimed at one decision, where a
    # diff of two whole solutions has to be found first
    return [
        f"<mutant change={mutant.change!r} line={mutant.line}>",
        mutant.code,
        "</mutant>",
        "",
    ]


class ProposedCase(BaseModel):
    """One case as the reply proposes it: the arguments and nothing else."""

    # no mutant named: which one an input catches is settled by running it, and
    # a claim nothing checks would be stored beside cases that are checked
    args: list[Any]

    @field_validator("args", mode="before")
    @classmethod
    def _decoded(cls, value: Any) -> Any:
        # as `DraftCase`: strict structured output cannot express an
        # unconstrained JSON value, so the arguments arrive as text
        return json.loads(value) if isinstance(value, str) else value


class Proposed(BaseModel):
    cases: list[ProposedCase] = Field(min_length=1)


def read(text: str) -> list[list[Any]]:
    return [case.args for case in Proposed.model_validate_json(text).cases]


def schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "args": {
                            "type": "string",
                            "description": "JSON array of the positional arguments",
                        },
                    },
                    "required": ["args"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["cases"],
        "additionalProperties": False,
    }


def separators(
    transport: Transport,
    log: CallLog,
    statement: str,
    *,
    canonical: str,
    survivors: Sequence[Mutant],
    known: Sequence[Sequence[Any]] = (),
    configuration: Configuration = DISCRIMINATION_DEFAULT,
) -> tuple[list[list[Any]], Call]:
    """The arguments proposed for the survivors, and the call that wrote them.

    One call for all of them: a proposal that separates nothing costs the case
    it would have added, where a bad entry in a batched reply costs the batch.
    """
    if not survivors:
        raise ValueError("no survivor to answer")

    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(statement, canonical, survivors, known),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(),
    )
    if text is None:
        raise GenerationError(call.error or "no cases")
    return read(text), call


__all__ = [
    "SYSTEM",
    "Proposed",
    "ProposedCase",
    "already",
    "prompt",
    "read",
    "schema",
    "separators",
    "shown",
]
