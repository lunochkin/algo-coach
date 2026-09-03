"""What a transport returns, and what one is. Nothing above a transport sees a
provider's own response shape."""

from dataclasses import dataclass
from typing import Any, Protocol

# Thinking and answer together: no model reached through this transport accepts
# a separate reasoning budget. Sized against a runaway, not against a reading —
# one generation call spent 11,520 tokens thinking and had 466 left for a
# statement, which arrived cut in half and parsed as nothing.
MAX_TOKENS = 32000


class ProviderError(Exception):
    """A 200 carrying an error and no choices, or a choice that stopped on one:
    how the router reports that whoever it picked failed. `code` is the status
    inside that body, and is all that separates a gateway failure from a
    rejected schema."""

    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Reply:
    text: str | None  # None where the model answered nothing: a refusal, or cut short
    thinking: str | None = None
    stop_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    cost: float | None = None  # always returned; absent only if the provider reported none
    provider: str | None = None  # the company the router reports, not the endpoint
    request_ms: int | None = None  # this request alone; a caller's own timing includes backoff
    attempts: int | None = None


@dataclass(frozen=True)
class Trace:
    """A failure's own count and timing. Stamped on the exception rather than
    wrapped around it, so every caller still catches the type it caught before."""

    attempts: int
    request_ms: int


@dataclass(frozen=True)
class Retry:
    """One transient failure, reported while it is being waited out: no record
    holds the wait itself, and a run behind a per-minute cap is silent."""

    status: int | None
    model: str
    pin: str
    tries: int  # the request that just failed, 1-based
    of: int  # how many it will make in all
    pause: float  # seconds about to be slept
    reason: str


def stamp(exc: Exception, trace: Trace) -> None:
    exc.__dict__["trace"] = trace


def traced(exc: Exception) -> Trace | None:
    trace = exc.__dict__.get("trace")
    return trace if isinstance(trace, Trace) else None


class Transport(Protocol):
    """Send one prompt and come back with a `Reply`, or raise."""

    def __call__(
        self,
        *,
        system: str,
        content: str,
        model: str,
        effort: str,
        pin: str,
        temperature: float | None,
        schema: dict[str, Any] | None,
        max_tokens: int,
    ) -> Reply: ...
