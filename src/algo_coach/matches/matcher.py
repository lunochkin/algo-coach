"""Which of a card's templates a problem exercises.

A question about what the problem asks, so the statement is the evidence: a
technique says what it is about, and a form is how it is solved. The same shape as
the technique classifier — candidates in, the subset out — read by a prompted
model for the same reason, that nobody has labelled which form solves what.
"""

import json
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel

from algo_coach.calls import CallLog, Transport, ask
from algo_coach.calls import prompt_hash as digest
from algo_coach.schema import Call, Card, Problem, Template, TemplateKind

MODEL = "openai/gpt-oss-120b"
EFFORT = "medium"
PIN = "deepinfra/bf16"
# Greedy, as every reading written into the log is: the verdict a model holds
# at 0.9 must not land as a coin flip in a record the ladder is derived from.
TEMPERATURE: float | None = 0.0

SYSTEM = """You decide which of a card's templates a problem exercises.

The candidates are the forms one card teaches, each with the cue that says to
reach for it and the code it comes back as. Say which of them a correct
solution to the problem in front of you is built out of.

Name every one that applies and nothing more. Two approaches to one problem is
ordinary, so more than one candidate can be right; a candidate that merely
could be bent to fit is not.

Decide from what the problem asks, not from what it is about. A problem's
subject is the technique; a template is the shape of the solution, and two
problems on one technique are often different forms.

If the problem exercises none of the candidates, name none of them."""


class Configuration(BaseModel, frozen=True):
    """Which matcher read a pair, and the key its records are found under.

    Its own rather than the claim classifier's: the two ask different
    questions, and the model that reads code well is not by that fact the one
    that reads a statement well. The prompt is not among the fields — it varies
    per pair, so what rulebook a reading came from is the digest of what that
    pair was sent.
    """

    model: str = MODEL
    effort: str = EFFORT
    pin: str = PIN
    temperature: float | None = TEMPERATURE


DEFAULT = Configuration()


class MatcherError(Exception):
    """The model returned no verdict — a refusal, or an answer cut short."""


def candidates(card: Card) -> list[Template]:
    """The templates a problem is tested against.

    Procedure templates are excluded: a framing procedure is exercised by every
    problem its technique reaches, so a per-problem verdict on one carries no
    information. The ladder covers it as a whole instead.
    """
    return [template for template in card.templates if template.kind is not TemplateKind.PROCEDURE]


def request_hash(card: Card, problem: Problem) -> str:
    """The digest of what this pair would be sent, right now.

    Per pair for the same reason a claim's is per attempt: a template edited on
    one card re-tests that card's pairs and leaves every other one settled.
    """
    return digest(SYSTEM, prompt(candidates(card), problem))


def match(
    transport: Transport,
    log: CallLog,
    card: Card,
    problem: Problem,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """The slugs of the templates this problem exercises, and the call that
    read them — `None` where there was nothing to ask.

    One call per problem and card, never per pair: the candidates are that
    card's templates and the answer is the subset, which is the classifier's
    shape and one request rather than six. The records come from the one
    answer.

    A single candidate is still asked about, unlike a lone technique: there
    the problem's own techniques already answer, here the verdict is the
    record, and yes and no are both readings that have to be paid for once.
    """
    forms = candidates(card)
    if not forms:
        return [], None

    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(forms, problem),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(forms),
    )
    if text is None:
        raise MatcherError(call.error or "no verdict")

    # Checked again because the schema's guarantee ends with the request and
    # the record does not.
    named = set(json.loads(text)["templates"])
    return [template.slug for template in forms if template.slug in named], call


def prompt(forms: Sequence[Template], problem: Problem) -> str:
    """The candidates before the problem, so the reading is made knowing what
    can be named. Delimited, since a statement is data the model reads rather
    than instructions it follows."""
    return "\n".join(
        [
            f"Candidates: {', '.join(template.slug for template in forms)}",
            "",
            *(line for template in forms for line in block(template)),
            f"<problem title={problem.title!r}>",
            problem.statement,
            "</problem>",
        ]
    )


def block(template: Template) -> list[str]:
    """One candidate as its reader meets it: what it is, when it fires, and
    the form itself. The code is what a template *is* — a cue alone would ask
    the model to match a name it has to guess the shape of."""
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
