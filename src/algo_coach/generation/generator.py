"""Writing a problem for one template: the statement, the canonical solution
and the first test cases.

One call for all three. Cases asked for after a solution exists describe
whatever that solution happens to do, where cases written beside the statement
describe what the problem asks. The same call is why the statement comes
first in the brief: the code and the cases are asked to follow from it.

One response schema over all three parts, so a reply carrying two of them
fails at the request rather than landing a problem with a part to fill in
later. Nothing is stored from here: what the reply becomes is decided after
the canonical and the reference have run.
"""

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator

from algo_coach.schema import Card, Template

SYSTEM = """You write practice problems for one form of a technique.

You are given a template: a form a solver reproduces from memory, its cue, and
the code it comes back as. Write a problem that this form solves.

Produce three things.

1. A statement. Self-contained prose: what the input is, what to return, the
   constraints that bound them, and one worked example. It must not name the
   technique, the template, or the data structure the solution uses. The solver
   has to derive the form from what is asked.
2. A canonical solution. Python, one module-level function named `solve`,
   taking its arguments positionally. Written to display the form rather than
   to be clever.
3. Test cases. Each is the positional arguments and the expected return.
   Include the edge cases the statement admits. They must separate a correct
   solution from a plausible wrong one: a solution that handles the ordinary
   input and gets the boundary wrong has to fail at least one case.

The cue and the notes name concrete settings so the form is recognisable: a
domain, an object, a scenario. Your statement uses none of them. Such a setting
is usually the published problem the cue was written from, and a solver who
recognises that problem has not derived its form. Choose a setting neither the
cue nor the notes mentions.

Write the statement first, and let the solution and the cases follow from it.
Cases read off a finished solution test what that code does rather than what
the problem asks.

The statement admits one reading. Another solver will write a solution from it
alone, and a disagreement between the two discards the problem. State how ties
are broken and what an empty input returns.

A case carries two JSON texts. `args` is an array of the positional arguments,
in the order `solve` takes them. `expected` is the value `solve` must return.
Both are written as JSON inside a string, so a string keeps its quotes and an
absent value is `null`."""


def prompt(card: Card, template: Template) -> str:
    """The brief: one form, and the technique it belongs to.

    The technique's cue is carried beside the template's because they answer
    different questions. One says when to reach for the technique at all, the
    other which of its forms is being asked for. A brief holding only the
    second would leave the model to infer the subject from a form.

    The form itself is sent, as it is to the matcher. A cue and a title name a
    shape the model would otherwise have to guess at.
    """
    return "\n".join(
        [
            f"Technique: {card.technique}",
            f"Reach for it when: {card.trigger}",
            "",
            f"Template: {template.title}",
            f"Cue: {template.trigger}",
            *notes(template),
            "Form:",
            *(f"  {line}" for line in template.code.splitlines()),
        ]
    )


def notes(template: Template) -> list[str]:
    """What to read about this form, where the template carries it. Absent
    rather than empty: a labelled heading with nothing under it reads as a
    field the author left blank."""
    if template.notes is None:
        return []
    return ["Notes:", *(f"  {line}" for line in template.notes.splitlines())]


class DraftCase(BaseModel):
    """One case as the generator wrote it: the arguments and what `solve` must
    return.

    Not a `TestCase`. It carries no id and no problem, because neither exists
    until the problem lands, and it names no `expected_from` — the first set
    is recomputed from the reference before anything is stored.
    """

    args: list[Any]
    expected: Any

    @field_validator("args", "expected", mode="before")
    @classmethod
    def _decoded(cls, value: Any) -> Any:
        """The two arrive as JSON text and are decoded here.

        Strict structured output cannot express an unconstrained JSON value:
        every object states its properties and every array its items, so a
        field holding "whatever the problem's arguments are" has no schema. A
        string does, and what it holds is checked on arrival rather than by the
        provider. Text that does not parse fails the reply, which is the same
        outcome one missing part gets.
        """
        return json.loads(value) if isinstance(value, str) else value


class Draft(BaseModel):
    """What one generation call returns, before anything has run.

    Called a draft because none of it is established yet: the canonical has not
    met the cases, no reference has agreed with it, and a problem that fails
    either is discarded whole.
    """

    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    # the canonical, in the role it was asked for. The reference is a second
    # call from the statement alone, so it is not part of this reply
    canonical: str = Field(min_length=1)
    # what decides the problem. A draft carrying none decides nothing, and a
    # problem does not land without the cases that judge it
    cases: list[DraftCase] = Field(min_length=1)


def read(text: str) -> Draft:
    """The reply as the three parts it has to be.

    Checked again on arrival because the schema's guarantee ends with the
    request. A provider that answered without honouring it, or honoured it and
    wrote `args` that is not JSON, fails here instead of storing a problem
    whose cases nothing can run.
    """
    return Draft.model_validate_json(text)


def schema() -> dict[str, Any]:
    """The one shape all three parts come back in.

    Fixed rather than built per call, unlike the matcher's: there the
    candidates are the enum, where a problem is the same object whatever
    template it was written for.

    Every property is required and none is added, which is what `strict` means
    at the endpoint. A reply missing the canonical is then a failed request,
    not a stored problem waiting for a second call to complete it.
    """
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "statement": {"type": "string"},
            "canonical": {"type": "string"},
            "cases": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "args": {
                            "type": "string",
                            "description": "JSON array of the positional arguments",
                        },
                        "expected": {
                            "type": "string",
                            "description": "JSON value `solve` must return",
                        },
                    },
                    "required": ["args", "expected"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["title", "statement", "canonical", "cases"],
        "additionalProperties": False,
    }
