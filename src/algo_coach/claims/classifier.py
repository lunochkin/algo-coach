"""Which of a problem's techniques a solution used.

A prompted model reading the code, not a trained one: public corpora tag
problems, not solutions, so a model trained on them would predict the fallback
rather than improve on it.
"""

import json
from collections.abc import Sequence
from hashlib import sha256
from typing import Any

from pydantic import BaseModel

from algo_coach.techniques import criteria

MODEL = "claude-opus-5"
EFFORT = "medium"
# The effort of a model that is asked for none — some reject the parameter
# outright. A named level rather than an absent field, since a reading whose
# configuration is partly unknown compares with nothing: what it ran at is the
# model's own default, which is a fact about the reading and not a gap in it.
UNSENT = "default"
# Bumped when the reading changes meaningfully — the author's statement, not a
# number to be greater than. The effort is recorded beside it rather than
# folded into it, so a bump says the prompt changed and nothing else.
PROMPT_VERSION = "4"

SYSTEM = """You name which techniques a solution used.

The candidates are one problem's tags — what the problem could exercise. Say
which of them the code in front of you actually did. Name every one it used
and nothing more: a solution can combine several, and one naming every
candidate agrees with the tags and decides nothing.

Each candidate carries what earns it and the near miss it is confused with.
Decide each against its own rule, and where the code fits the near miss
instead, do not name it.

Name a candidate even when a narrower one also applies. What a solution does
can be true at more than one level, and every level it did is claimed — never
withhold a code because another candidate covers it. An entry that is an
exception to this says so.

What disqualifies a candidate is incidental use: the technique appears in the
code without being part of how the solution works. Read for the invariant, not
the syntax, and let each candidate's near miss say where that line falls.

If the code used none of the candidates, name none of them."""

# The mechanical fact of the instructions sent, marking nothing. A forgotten
# version bump is otherwise invisible forever; with both, two hashes under one
# version say so. Twelve hex characters of sha256 over SYSTEM: only ever
# compared for equality, and the candidates and the code vary per attempt, so
# hashing the rendered prompt would identify a call rather than a
# configuration.
PROMPT_HASH = sha256(SYSTEM.encode()).hexdigest()[:12]


class Configuration(BaseModel, frozen=True):
    """Which classifier a reading came from, and the key it is found under.

    Three fields, not the record's four: the hash is this build's `SYSTEM` text
    rather than something a caller selects, so it is stamped on the write path
    and keyed off nowhere. Frozen because it is an identity — compared whole,
    never ordered, so a rollback is naming the earlier one.
    """

    model: str = MODEL
    effort: str = EFFORT
    prompt_version: str = PROMPT_VERSION


DEFAULT = Configuration()


class ClassifierError(Exception):
    """The model returned no verdict — a refusal, or an answer cut short."""


def classify(
    client: Any, candidates: Sequence[str], code: str, *, configuration: Configuration = DEFAULT
) -> list[str]:
    """The techniques a solution used, chosen from the problem's own tags.

    The candidates appear twice, doing different jobs. The response schema
    enforces them, so the classifier cannot name a technique the tags do not.
    The prompt informs them: thinking is not schema-constrained, so a model
    that met the candidates only at emission time would reason about the code
    without knowing which answers exist, then be forced into the nearest one.

    The code is the only evidence beyond them: a title or a statement
    describes what the problem admits, which is the question the fallback
    already answers.

    Naming nothing is legal — the tags may not cover what the code did, and no
    claim leaves the fallback standing rather than asserting a wrong one.
    """
    if len(candidates) < 2:
        # Nothing to decide: the fallback already says this, and a schema
        # offering one choice would ask the model to agree with itself.
        return list(candidates)

    output_config: dict[str, Any] = {
        "format": {"type": "json_schema", "schema": schema(candidates)}
    }
    if configuration.effort != UNSENT:
        # Sent only where it was asked for: a model that does not take the
        # parameter rejects every call carrying it, whatever the level.
        output_config["effort"] = configuration.effort

    response = client.messages.create(
        model=configuration.model,
        max_tokens=16000,
        system=SYSTEM,
        output_config=output_config,
        messages=[{"role": "user", "content": prompt(candidates, code)}],
    )
    text = next((block.text for block in response.content if block.type == "text"), None)
    if text is None:
        raise ClassifierError(f"no verdict: {response.stop_reason}")

    # Checked again because the schema's guarantee ends with the request and
    # the record does not: an append-only log has no pass that fixes a bad
    # code later.
    named = set(json.loads(text)["techniques"])
    return [technique for technique in candidates if technique in named]


def prompt(candidates: Sequence[str], code: str) -> str:
    """The candidates and their criteria before the code, so the reading is
    made knowing what can be named and what earns each one. Delimited, since
    the code is data the model reads rather than instructions it follows.

    Beside the candidates rather than in the system text: a criterion is a
    per-code rule, and one carried by every call is paid for on the calls
    where its code is not a candidate — which, over a vocabulary of this size,
    is nearly all of them.
    """
    return "\n".join(
        [
            f"Candidates: {', '.join(candidates)}",
            "",
            *(line for candidate in candidates for line in criterion(candidate)),
            "<solution>",
            code,
            "</solution>",
        ]
    )


def criterion(candidate: str) -> list[str]:
    """One candidate's rule, and nothing for a code the vocabulary no longer
    carries. Records outlive the vocabulary, so a retired code can still be a
    candidate; it then reaches the model as a bare name, which is what the
    prompt said before any criterion existed.

    The kind arrives as its test rather than as its name: one question is
    answered four ways, and a bare label only helps a reader who already knows
    which way. Naming it is what keeps a structure from being judged on whether
    it was performed."""
    entry = criteria().get(candidate)
    if entry is None:
        return []
    return [
        f"{entry.code} — {entry.kind}: {entry.kind.test}.",
        f"  Earns it: {entry.earns}",
        f"  Near miss: {entry.near_miss}",
        "",
    ]


def schema(candidates: Sequence[str]) -> dict[str, Any]:
    """The same candidates as an enum. The prompt informs the reading; this
    enforces it — an instruction can be violated, a response format cannot."""
    return {
        "type": "object",
        "properties": {
            "techniques": {"type": "array", "items": {"type": "string", "enum": list(candidates)}},
        },
        "required": ["techniques"],
        "additionalProperties": False,
    }
