"""Which of a card's templates a solution displays. Candidates in, the subset
out, as the technique classifier works."""

import json
from collections.abc import Sequence
from typing import Any

from algo_coach.calls import CallLog, Transport, ask
from algo_coach.calls import prompt_hash as digest
from algo_coach.schema import Call, Card, Configuration, Problem, Solution, Template, TemplateKind

MODEL = "openai/gpt-oss-120b"
EFFORT = "medium"
PIN = "deepinfra/bf16"
# Greedy, as every reading written into the log is.
TEMPERATURE: float | None = 0.0

SYSTEM = """You decide which of a card's templates a solution displays.

The candidates are the forms one card teaches, each with the cue that says to
reach for it and the code it comes back as. Say which of them the solution in
front of you is built out of.

Name every one that applies and nothing more. One solution can compose two
forms, so more than one candidate can be right; a candidate that merely could
be bent to fit is not.

Decide from the code, not from the problem's subject. That subject is the
technique; a template is the shape of the solution, and two solutions to one
problem are often different forms.

The statement is there for what the code leaves implicit, never as the verdict.

If the solution displays none of the candidates, name none of them."""


# Which matcher read a pair. The prompt is not among them: it varies per pair,
# so what a reading came from is the digest of what that pair was sent.
DEFAULT = Configuration(model=MODEL, effort=EFFORT, pin=PIN, temperature=TEMPERATURE)


class MatcherError(Exception):
    """The model returned no verdict — a refusal, or an answer cut short."""


def candidates(card: Card) -> list[Template]:
    return [template for template in card.templates if template.kind is not TemplateKind.PROCEDURE]


# Per pair, so a template edited on one card re-tests that card and leaves
# every other pair settled.
def request_hash(card: Card, problem: Problem, solution: Solution) -> str:
    return digest(SYSTEM, prompt(candidates(card), problem, solution))


def match(
    transport: Transport,
    log: CallLog,
    card: Card,
    problem: Problem,
    solution: Solution,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """The slugs of the templates this solution displays, and the call that
    read them — `None` where there was nothing to ask.

    One call per solution and card, never per pair: every record comes from the
    one answer. A lone candidate is still asked about, since a negative verdict
    is a record too.
    """
    forms = candidates(card)
    if not forms:
        return [], None

    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(forms, problem, solution),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(forms),
    )
    if text is None:
        raise MatcherError(call.error or "no verdict")

    # Checked again: the schema binds the request, not the record.
    named = set(json.loads(text)["templates"])
    return [template.slug for template in forms if template.slug in named], call


def prompt(forms: Sequence[Template], problem: Problem, solution: Solution) -> str:
    """The candidates first, so the reading is made knowing what can be named,
    then the statement and the code that answers it. Both are delimited: they
    are data the model reads rather than instructions it follows."""
    return "\n".join(
        [
            f"Candidates: {', '.join(template.slug for template in forms)}",
            "",
            *(line for template in forms for line in block(template)),
            f"<problem title={problem.title!r}>",
            problem.statement,
            "</problem>",
            "<solution>",
            solution.code.rstrip(),
            "</solution>",
        ]
    )


def block(template: Template) -> list[str]:
    """One candidate: what it is, when it fires, and the form itself. A cue
    without the code would ask the model to guess the shape of a name."""
    return [
        f"{template.slug} — {template.title}",
        f"  Cue: {template.trigger}",
        "  Form:",
        *(f"    {line}" for line in template.code.splitlines()),
        "",
    ]


def schema(forms: Sequence[Template]) -> dict[str, Any]:
    """The same candidates as an enum: the prompt informs the reading, this
    enforces it."""
    return {
        "type": "object",
        "properties": {
            "templates": {
                "type": "array",
                "items": {"type": "string", "enum": [template.slug for template in forms]},
            },
        },
        "required": ["templates"],
        "additionalProperties": False,
    }
