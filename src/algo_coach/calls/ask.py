"""Making a call and recording it, with nothing said about what it was for.

The half of a classification that is not the transport: a caller hands over
the text and the schema it wants back, and gets the answer and the id of the
record that now holds it. What the answer means is the caller's; how it was
fetched is the transport's.
"""

from hashlib import sha256
from time import monotonic
from typing import Any

from algo_coach.calls.store import CallLog
from algo_coach.calls.transport import MAX_TOKENS, Reply, Transport, traced
from algo_coach.mint import call as mint_call
from algo_coach.schema import Call

# Twelve hex characters of sha256. Only ever compared for equality, so the
# collision margin is irrelevant beside carrying sixty-four of them on every
# line of an append-only log.
HASH_LENGTH = 12


def payload(system: str, content: str) -> str:
    """The prompt as one string: what was sent, in the order it was sent.

    Hashed and stored in this form, so the stored text digests to the hash
    beside it and a renderer that changes cannot make an old record unreadable.
    """
    return f"{system}\n\n---\n\n{content}"


def prompt_hash(system: str, content: str) -> str:
    return sha256(payload(system, content).encode()).hexdigest()[:HASH_LENGTH]


def ask(
    transport: Transport,
    log: CallLog,
    *,
    system: str,
    content: str,
    model: str,
    effort: str,
    pin: str,
    temperature: float | None = None,
    schema: dict[str, Any] | None = None,
    max_tokens: int = MAX_TOKENS,
) -> tuple[Call, str | None]:
    """Send one prompt, record what happened, and return the call and its text.

    A failure is recorded too, then raised. The caller decides whether one
    attempt's problem ends the run, and the record is what makes a run that
    broke overnight readable afterwards. Only the message and the exception's
    type are kept. A repr can carry request context, and this file outlives the
    terminal it would have been printed to.

    The output schema is not part of the hash. It is built from the candidates,
    which already appear verbatim in the content, so it varies with nothing the
    hash does not already cover.

    The whole wait is timed here, so a retried call records what it cost the
    run. The last request's time and the count come back from the transport,
    which is the only thing that sees them. A monotonic clock is used: a wall
    clock stepping backwards would record a negative wait.
    """
    text = payload(system, content)
    digest = prompt_hash(system, content)
    started = monotonic()

    try:
        reply = transport(
            system=system,
            content=content,
            model=model,
            effort=effort,
            pin=pin,
            temperature=temperature,
            schema=schema,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        log.append(
            mint_call(
                model=model,
                effort=effort,
                prompt=text,
                prompt_hash=digest,
                pin=pin,
                temperature=temperature,
                error=f"{type(exc).__name__}: {exc}",
                elapsed_ms=elapsed(started),
                **failed(exc),
            )
        )
        raise

    call = mint_call(
        model=model,
        effort=effort,
        prompt=text,
        prompt_hash=digest,
        pin=pin,
        temperature=temperature,
        # A reply with no text answered nothing — a refusal, or an answer cut
        # short. Recorded as the failure it is, so the log does not claim an
        # empty verdict was a reading.
        response=reply.text,
        error=None if reply.text is not None else f"no verdict: {reply.stop_reason}",
        thinking=reply.thinking,
        stop_reason=reply.stop_reason,
        input_tokens=reply.input_tokens,
        output_tokens=reply.output_tokens,
        provider=reply.provider,
        elapsed_ms=elapsed(started),
        request_ms=reply.request_ms,
        attempts=reply.attempts,
    )
    log.append(call)
    return call, reply.text


def failed(exc: Exception) -> dict[str, int]:
    """What the transport stamped, or nothing — which leaves the fields absent
    rather than claiming a request nobody counted."""
    trace = traced(exc)
    return {} if trace is None else {"attempts": trace.attempts, "request_ms": trace.request_ms}


def elapsed(started: float) -> int:
    """Milliseconds, since nothing reads a call's timing more finely than that
    and a float would carry precision the clock never had."""
    return round((monotonic() - started) * 1000)


__all__ = ["HASH_LENGTH", "Reply", "Transport", "ask", "payload", "prompt_hash"]
