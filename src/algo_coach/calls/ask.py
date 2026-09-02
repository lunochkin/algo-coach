"""Making a call and recording it, with nothing said about what it was for."""

from hashlib import sha256
from time import monotonic
from typing import Any

from algo_coach.calls.store import CallLog
from algo_coach.calls.transport import MAX_TOKENS, Reply, Transport, traced
from algo_coach.mint import call as mint_call
from algo_coach.schema import Call

# Hex characters of sha256, compared only for equality; sixty-four of them
# would be carried on every line of an append-only log.
HASH_LENGTH = 12


# Hashed and stored in this form, so a stored prompt digests to the hash beside it.
def payload(system: str, content: str) -> str:
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

    A failure is recorded before it is re-raised, keeping the message and the
    exception type but never a repr, which can carry request context. The
    schema is not part of the hash: it is built from the candidates, which
    appear verbatim in the content already.
    """
    text = payload(system, content)
    digest = prompt_hash(system, content)
    # Monotonic: a wall clock stepping backwards would record a negative wait.
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
        # No text is a refusal or a cut-short answer, recorded as the failure it
        # is rather than as an empty verdict.
        response=reply.text,
        error=None if reply.text is not None else f"no verdict: {reply.stop_reason}",
        thinking=reply.thinking,
        stop_reason=reply.stop_reason,
        input_tokens=reply.input_tokens,
        output_tokens=reply.output_tokens,
        cost=reply.cost,
        reasoning_tokens=reply.reasoning_tokens,
        provider=reply.provider,
        elapsed_ms=elapsed(started),
        request_ms=reply.request_ms,
        attempts=reply.attempts,
    )
    log.append(call)
    return call, reply.text


def failed(exc: Exception) -> dict[str, int]:
    """What the transport stamped, or nothing where it never retried."""
    trace = traced(exc)
    return {} if trace is None else {"attempts": trace.attempts, "request_ms": trace.request_ms}


def elapsed(started: float) -> int:
    return round((monotonic() - started) * 1000)


__all__ = ["HASH_LENGTH", "Reply", "Transport", "ask", "payload", "prompt_hash"]
