"""Writing a problem for one template: the statement, the canonical solution,
the first test cases and how hard it is. One call for all of them."""

import json
from collections.abc import Iterable, Sequence
from typing import Any

from pydantic import BaseModel, Field, field_validator

from algo_coach.calls import CallLog, Configuration, Transport, ask
from algo_coach.generation.errors import GenerationError
from algo_coach.schema import Call, Card, Problem, ProblemDifficulty, Template

# unmeasured: none of the gates a generator is scored by has run yet. Sampled
# where the other three are greedy, and `machine.md` gives the reason. Pinned to
# AI Studio rather than Vertex, whose endpoints advertise no temperature
GENERATOR_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio"
)

SYSTEM = """You write practice problems for one form of a technique.

You are given a template: a form a solver reproduces from memory, its cue, and
the code it comes back as. Write a problem that this form solves.

Produce four things.

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
4. A difficulty: easy, medium or hard. Easy is the form applied to what the
   statement hands over. Medium needs the input transformed, or a state
   chosen, before the form fits. Hard makes the form one step of a solution
   whose rest has to be derived. Judge the problem you wrote, not the form.

The cue and the notes name concrete settings so the form is recognisable: a
domain, an object, a scenario. Your statement uses none of them. Such a setting
is usually the published problem the cue was written from, and a solver who
recognises that problem has not derived its form. Choose a setting neither the
cue nor the notes mentions.

Any statements already written for this form are listed after the brief. Yours
asks a different question. The same question in a new setting is a variant, and
ten variants of one problem teach the form once.

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


def prompt(card: Card, template: Template, written: Sequence[str] = ()) -> str:
    """The brief: one form, and the technique it belongs to.

    Both cues, since they answer different questions: when to reach for the
    technique, and which of its forms is asked for. `written` is what this
    form already has — unseen, a model writes the problem the form suggests,
    which is the same problem every run.
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
            *already(written),
        ]
    )


def already(written: Sequence[str]) -> list[str]:
    # delimited: each statement is data the model is told apart from, not
    # instructions it follows
    if not written:
        return []
    return [
        "",
        "Already written for this form:",
        *(line for statement in written for line in ("<written>", statement, "</written>")),
    ]


def notes(template: Template) -> list[str]:
    # absent rather than empty: a heading with nothing under it reads as a
    # field the author left blank
    if template.notes is None:
        return []
    return ["Notes:", *(f"  {line}" for line in template.notes.splitlines())]


class DraftCase(BaseModel):
    """One case as the generator wrote it: the arguments and what `solve` must
    return."""

    # no id, no problem and no `expected_from`: none of the three exists until
    # the problem lands, and the reference recomputes `expected` before it does
    args: list[Any]
    expected: Any

    @field_validator("args", "expected", mode="before")
    @classmethod
    def _decoded(cls, value: Any) -> Any:
        # strict structured output cannot express an unconstrained JSON value,
        # so the two arrive as text and are checked here, not by the provider
        return json.loads(value) if isinstance(value, str) else value


class Draft(BaseModel):
    """What one generation call returns, before anything has run."""

    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    # the reference is a second call from the statement alone, so it is not
    # part of this reply
    canonical: str = Field(min_length=1)
    cases: list[DraftCase] = Field(min_length=1)
    # asked for rather than derived: nothing else has read the problem yet
    difficulty: ProblemDifficulty


def read(text: str) -> Draft:
    # checked again on arrival: the schema's guarantee ends with the request
    return Draft.model_validate_json(text)


def schema() -> dict[str, Any]:
    # fixed rather than built per call, unlike the matcher's: a problem is the
    # same object whatever template it was written for
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "statement": {"type": "string"},
            "canonical": {"type": "string"},
            "difficulty": {"type": "string", "enum": [one.value for one in ProblemDifficulty]},
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
        "required": ["title", "statement", "canonical", "difficulty", "cases"],
        "additionalProperties": False,
    }


def generate(
    transport: Transport,
    log: CallLog,
    card: Card,
    template: Template,
    *,
    written: Sequence[str] = (),
    configuration: Configuration = GENERATOR_DEFAULT,
) -> tuple[Draft, Call]:
    # the call is returned beside the draft because the problem, the cases and
    # the solution all copy their provenance from it
    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(card, template, written),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(),
    )
    if text is None:
        raise GenerationError(call.error or "no draft")
    return read(text), call


def written_for(problems: Iterable[Problem], template: Template) -> list[str]:
    # every status, retired included: what the next run differs from is the
    # corpus rather than the part of it that is served
    return [problem.statement for problem in problems if problem.generated_for == template.id]
