"""A reading that names a subset of the candidates it was offered, which is how
the classifier and the matcher both read. The candidates appear twice: the
schema enforces them, and the prompt informs them, thinking being unconstrained."""

import json
from collections.abc import Sequence
from typing import Any

from algo_coach.calls.ask import ask
from algo_coach.calls.store import CallLog
from algo_coach.calls.transport import Transport
from algo_coach.schema import Call, Configuration


def choice_schema(key: str, options: Sequence[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            key: {"type": "array", "items": {"type": "string", "enum": list(options)}},
        },
        "required": [key],
        "additionalProperties": False,
    }


def offer(
    transport: Transport,
    log: CallLog,
    *,
    system: str,
    content: str,
    key: str,
    options: Sequence[str],
    configuration: Configuration,
) -> tuple[Call, str | None]:
    """One request at the configuration, constrained to the options. What the
    text means is the caller's: a cut-short reply is a verdict to one reader
    and a failure to another."""
    return ask(
        transport,
        log,
        system=system,
        content=content,
        model=configuration.model,
        effort=configuration.effort,
        pin=configuration.pin,
        temperature=configuration.temperature,
        schema=choice_schema(key, options),
    )


def chosen(text: str, key: str, options: Sequence[str]) -> list[str]:
    """The options the reply named, in the order offered. Checked against them
    again: the schema's guarantee ends with the request, and an append-only log
    has no later pass that fixes a bad name."""
    named = set(json.loads(text)[key])
    return [one for one in options if one in named]


__all__ = ["choice_schema", "chosen", "offer"]
