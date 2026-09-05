"""Which techniques a piece of code used, chosen from candidates the caller
gives."""

import json
from collections.abc import Sequence
from typing import Any

from algo_coach.calls import CallLog, Transport, ask
from algo_coach.calls import prompt_hash as digest
from algo_coach.schema import Call, Configuration
from algo_coach.techniques import criterion

# Twenty configurations over the same 80 hand-claimed attempts spread 70% to
# 95%, and the leaders miss different attempts. This one is within a single
# attempt of the best at a twentieth of the price, and the slowest of them.
MODEL = "google/gemma-4-31b-it"
EFFORT = "medium"
# Named to the quantization: unpinned, the router picks a build per request.
PIN = "coreweave/fp4"
# greedy, as every reader is
TEMPERATURE: float | None = 0.0
SYSTEM = """You name which techniques a solution used.

The candidates are one problem's own techniques — what the problem could
exercise. Say which of them the code in front of you actually did. Name every
one it used and nothing more: a solution can combine several, and one naming
every candidate agrees with the fallback and decides nothing.

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


# which classifier a reading came from. The prompt is not among them: staleness
# keys on the digest of what was sent
DEFAULT = Configuration(model=MODEL, effort=EFFORT, pin=PIN, temperature=TEMPERATURE)


class ClassifierError(Exception):
    """The model returned no verdict — a refusal, or an answer cut short."""


def request_hash(candidates: Sequence[str], code: str) -> str:
    return digest(SYSTEM, prompt(candidates, code))


def classify(
    transport: Transport,
    log: CallLog,
    candidates: Sequence[str],
    code: str,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """The techniques the code used, and the call that read them — `None` where
    the answer cost nothing. The candidates appear twice: the schema enforces
    them, and the prompt informs them, thinking being unconstrained."""
    # A schema offering one choice would ask the model to agree with itself.
    if len(candidates) < 2:
        return list(candidates), None

    call, text = ask(
        transport,
        log,
        system=SYSTEM,
        content=prompt(candidates, code),
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=schema(candidates),
    )
    if call.stop_reason == "length":
        # Truncated, so no verdict. Named as nothing rather than raised:
        # greedy, so a re-run pays the whole cap to fail identically.
        return [], call
    if text is None:
        raise ClassifierError(call.error or "no verdict")

    # Checked again: the schema's guarantee ends with the request, and an
    # append-only log has no later pass that fixes a bad code.
    named = set(json.loads(text)["techniques"])
    return [technique for technique in candidates if technique in named], call


def prompt(candidates: Sequence[str], code: str) -> str:
    """Criteria go here rather than in the system text: a per-code rule carried
    by every call is paid for on the calls where its code is not a
    candidate."""
    return "\n".join(
        [
            f"Candidates: {', '.join(candidates)}",
            "",
            *(line for candidate in candidates for line in block(candidate)),
            "<solution>",
            code,
            "</solution>",
        ]
    )


# One candidate's rule and the blank that separates it from the next. A retired
# code costs its own lines, not the separator around a rule that is not there.
def block(candidate: str) -> list[str]:
    lines = criterion(candidate)
    return [*lines, ""] if lines else []


def schema(candidates: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "techniques": {"type": "array", "items": {"type": "string", "enum": list(candidates)}},
        },
        "required": ["techniques"],
        "additionalProperties": False,
    }
