"""Writing a problem for one template: the statement, the canonical solution,
the first test cases and how hard it is. One call for all of them."""

import ast
import json
from collections.abc import Iterable, Sequence
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from climb.calls import CallLog, Transport
from climb.generation.contract import ALONE, ENTRY, POSITIONAL, RUNTIME, SIGNATURE
from climb.generation.site import answer
from climb.schema import (
    Call,
    Card,
    Configuration,
    DraftCase,
    Gate,
    Problem,
    ProblemDifficulty,
    SiteOutcome,
    Template,
)

# unmeasured: none of the gates a generator is scored by has run yet. Sampled
# where the other three are greedy, and `machine.md` gives the reason. Pinned
# to AI Studio rather than Vertex, whose endpoints advertise no temperature
GENERATOR_DEFAULT = Configuration(
    model="google/gemini-3.7-flash", effort="medium", pin="google-ai-studio"
)

# item 4 restates the criteria in `corpus.md`, Difficulty ratings
SYSTEM = f"""You write practice problems for one form of a technique.

You are given a template: a form a solver reproduces from memory, its cue, and
the code it comes back as. Write a problem that this form solves.

Produce four things.

1. A statement. Self-contained prose: what the input is, what to return, and
   one worked example, then a section headed `### Constraints`. That section
   bounds every input, one bound per bullet: each list's length, each
   integer's range with its sign stated (whether it may be negative or zero),
   each string's length and alphabet. A solver picks an approach from those
   bounds, and a value left unbounded is one they have to guess. Every bound
   sits in that section, and the prose above it states none. It must not name
   the technique, the template, or the data structure the solution uses. The
   solver has to derive the form from what is asked. It ends with {SIGNATURE}. Two
   more solutions are written from this prose alone, and a parameter order
   they have to infer is one they can infer differently.
2. A canonical solution. {RUNTIME}, {ENTRY},
   {POSITIONAL}. Written to display the form rather than to be clever.
   {ALONE}
3. Test cases. Each is the positional arguments and the expected return.
   Include the edge cases the statement admits. They must separate a correct
   solution from a plausible wrong one: a solution that handles the ordinary
   input and gets the boundary wrong has to fail at least one case.
4. A difficulty: easy, medium or hard, as the public problem platforms label
   their problems. Check the levels in order, and the first that fits is the
   label. Judge the problem you wrote, not the form.
   - Easy: one basic form applied unchanged, or a direct approach that fits
     the limits. The basic forms are a binary search over a sorted array, a
     running sum or minimum, a window of fixed width over sums, a recurrence
     on the two previous terms, a lookup or a count in a hash map, two
     pointers over sorted input or compacting in place, a table of prefix
     sums, a sort then one scan, matching brackets on a stack, rewiring a
     linked list, an in-order or level-order tree walk, and a plain
     breadth-first or depth-first reach over a graph. The statement asks the form's own
     question about the input as given, so a solver who holds the form adapts
     only names and the return value.
   - Medium: one standard technique plus one step the statement does not
     name: transforming the input, choosing a state, or deriving the predicate
     a search runs on. A search for the smallest feasible capacity is medium,
     since the feasibility check is the derived step. Medium also covers the
     direct use of a form past the basics: a monotonic stack, a disjoint set, a
     topological order, a knapsack, a backtracking search, a choice per
     element under an adjacency ban.
   - Hard: a form few solvers hold, two techniques combined, or a step the
     statement gives no hint of. A sliding-window maximum on a deque and the
     largest rectangle in a histogram are hard even applied directly, and so
     are counting windows with exactly k distinct values by complement and
     placing n queens.

The value `solve` returns is compared exactly, so it is built from integers,
strings, booleans and lists of those. A problem whose answer is a ratio asks
for the numerator and the denominator, reduced. A floating-point value is
compared bit for bit, and two correct solutions computing one in different
orders disagree in the last bits, so the problem is then discarded.

Where nothing is listed as already written for this form, write the standard
problem the form is known by: the question it is usually taught with, in your
own words. A learner meets the form first on that question. Any setting will
do, the cue's own included.

Invent the worked example and every case. Do not reuse the example, the values
or the wording of any published problem. A question is free to reuse, and a
published statement's text and examples are not. Examples a screen found
reused in earlier drafts for this form are listed after the brief, and your
draft uses none of them.

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


# shown where the template claims a speedup. `content.md` gives what the claim
# requires of the statement, and why the statement is not bent to help the
# search
SPEEDUP = """
This form is faster than the naive approach it replaces, and the problem is
stored with an input that shows it: the naive approach runs over a time limit
and the form does not. So the constraints admit inputs of at least a hundred
thousand elements, since the stored input has to be large enough for the naive
approach to exceed that limit."""


def prompt(
    card: Card,
    template: Template,
    written: Sequence[str] = (),
    aim: ProblemDifficulty | None = None,
    refused: Sequence[str] = (),
) -> str:
    """The prompt: one form, and the technique it belongs to.

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
            *([SPEEDUP] if template.speedup else []),
            *aimed(aim),
            *already(written),
            *reused(refused),
        ]
    )


def aimed(aim: ProblemDifficulty | None) -> list[str]:
    if aim is None:
        return []
    return ["", f"Write a problem at difficulty {aim}, and label it {aim}."]


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


def reused(refused: Sequence[str]) -> list[str]:
    if not refused:
        return []
    return [
        "",
        "Rejected in earlier drafts for this form, as a published example reused:",
        *(line for detail in refused for line in ("<reused>", detail, "</reused>")),
    ]


def refused_for(outcomes: Iterable[SiteOutcome], template: Template) -> list[str]:
    # in the order they were written, so one log sends one prompt hash
    return [
        one.detail
        for one in sorted(outcomes, key=lambda one: (one.created_at, one.id))
        if one.gate is Gate.COPIED and one.target_template_id == template.id
    ]


def notes(template: Template) -> list[str]:
    # absent rather than empty: a heading with nothing under it reads as a
    # field the author left blank
    if template.notes is None:
        return []
    return ["Notes:", *(f"  {line}" for line in template.notes.splitlines())]


class GeneratedCase(DraftCase):
    @field_validator("args", "expected", mode="before")
    @classmethod
    def _decoded(cls, value: object) -> object:
        # strict structured output cannot express an unconstrained JSON value,
        # so the two arrive as text and are checked here, not by the provider
        return json.loads(value) if isinstance(value, str) else value


class Generated(BaseModel):
    """What one generation call returns, before anything has run. Apart from
    `Draft`, which is what the steps after it leave."""

    title: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    # the reference is a second call from the statement alone, so it is not
    # part of this reply
    canonical: str = Field(min_length=1)
    cases: list[GeneratedCase] = Field(min_length=1)
    # asked for rather than derived: nothing else has read the problem yet
    difficulty: ProblemDifficulty

    @model_validator(mode="after")
    def _the_statement_carries_the_signature(self) -> Generated:
        # corpus.md, "The statement carries the signature": three prompts read
        # the order off it
        named = parameters(self.statement)
        if named is None:
            raise ValueError("the statement ends with the `def solve(...)` line its cases pass")
        # skipped rather than raised: a canonical that does not parse fails
        # every case, which is the gate that rejects the draft
        mine = parameters(self.canonical)
        if mine is not None and mine != named:
            raise ValueError(f"the statement declares solve{named} and the canonical takes {mine}")
        return self


def parameters(text: str) -> tuple[str, ...] | None:
    """The parameter names of the last `def solve(` in a text, prose or code.

    The last one: a statement can mention the call before it declares it, and
    the declaration is what a reader takes the order from.
    """
    for start in reversed([one for one in range(len(text)) if text.startswith("def solve(", one)]):
        parsed = _parsed(text[start:])
        if parsed is not None:
            return parsed
    return None


def _parsed(text: str) -> tuple[str, ...] | None:
    # the header alone, since prose after it is not code and a canonical's
    # body would parse to the same names anyway. Stripped of the backticks and
    # the full stop a statement wraps it in, since the prompt writes it in them
    header = text.split("\n", 1)[0].strip().rstrip("`.:")
    try:
        tree = ast.parse(f"{header}:\n    pass")
    except SyntaxError:
        return None
    [function] = tree.body
    if not isinstance(function, ast.FunctionDef):
        return None
    # positional-only counted too: `solve(xs, /)` and `solve(xs)` are one order
    return tuple(one.arg for one in [*function.args.posonlyargs, *function.args.args])


def read(text: str) -> Generated:
    # checked again on arrival: the schema's guarantee ends with the request
    return Generated.model_validate_json(text)


def schema() -> dict[str, Any]:
    # fixed rather than built per call, unlike the matcher's: a problem is the
    # same object whatever template it was written for
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "statement": {
                "type": "string",
                "description": f"prose ending with {SIGNATURE}",
            },
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
    aim: ProblemDifficulty | None = None,
    refused: Sequence[str] = (),
    configuration: Configuration = GENERATOR_DEFAULT,
) -> tuple[Generated, Call]:
    # the call is returned beside the draft because the problem, the cases and
    # the solution all copy their provenance from it
    text, call = answer(
        transport,
        log,
        system=SYSTEM,
        content=prompt(card, template, written, aim, refused),
        schema=schema(),
        configuration=configuration,
        missing="no draft",
    )
    return read(text), call


def written_for(problems: Iterable[Problem], template: Template) -> list[str]:
    # every status, retired included: what the next run differs from is the
    # corpus rather than the part of it that is served
    return [problem.statement for problem in problems if problem.target_template_id == template.id]
