"""One answering site's request, as every site makes it."""

from typing import Any

from algo_coach.calls import CallLog, Transport, ask
from algo_coach.generation.errors import GenerationError
from algo_coach.schema import Call, Configuration


def answer(
    transport: Transport,
    log: CallLog,
    *,
    system: str,
    content: str,
    schema: dict[str, Any],
    configuration: Configuration,
    missing: str,
) -> tuple[str, Call]:
    """The reply's text and the call that carried it. No text is a refusal or
    a cut-short reply, raised naming what the site did not write, since a run
    counts the failure rather than reading a verdict into it."""
    call, text = ask(
        transport, log, system=system, content=content, configuration=configuration, schema=schema
    )
    if text is None:
        raise GenerationError(call.error or missing)
    return text, call


__all__ = ["answer"]
