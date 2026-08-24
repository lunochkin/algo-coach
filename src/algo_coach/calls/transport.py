"""What a transport returns, and what one is.

The shape a provider answers in is the provider's. What the log records is
ours. `Reply` is the line between them: a transport turns one API's response
into this, and nothing above it ever sees a content block or a choice.

One shape at a time, by rule. Two provider shapes maintained by hand would
create pressure to adopt a library that reconciles them. Such a library can
downgrade a schema into a prompt, and the record would not show it happened.
"""

from dataclasses import dataclass
from typing import Any, Protocol

# What one reading may generate, thinking and answer together. There is no
# separate cap for the two: no model reached through this transport accepts a
# reasoning budget, and one sent to a provider that cannot honour it would be
# dropped by `require_parameters` rather than ignored.
#
# Set by what a runaway may cost rather than by what a reading needs. The
# second is per model and unknowable in advance — a verdict is a dozen tokens,
# but the thinking before it ran past 4000 on one model while another had never
# exceeded 1220. What a cap decides is only whether a reading happens: a
# truncated reply carries no verdict, so nothing is stored and nothing scored.
MAX_TOKENS = 12000


class ProviderError(Exception):
    """The endpoint answered, and the answer holds no answer.

    A 200 carrying an error and no choices, or a choice that stopped on one,
    which is how a router reports that whoever it picked failed. Raised rather
    than returned as an empty reply: nothing was read, so there is no reading
    to record — only a call that failed, and a message saying whose fault it
    was.

    `code` is the status the provider reported inside that body, where it gave
    one. A gateway failure and a rejected schema arrive by the same path and
    only the code separates them: one is worth asking again, the other is the
    configuration being wrong.
    """

    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Reply:
    """One answer, in the terms the call log keeps.

    `text` is None where the model answered nothing — a refusal, or an answer
    cut short. That is a failure rather than an empty reading, and `ask`
    records it as one.
    """

    text: str | None
    thinking: str | None = None
    stop_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    # What the router says the call cost. Always returned, so it needs no
    # parameter; absent only where a provider reported none.
    cost: float | None = None
    # Who actually served it — the name the router reports, which is the
    # company rather than the endpoint. The build asked for is the request's
    # own `pin`; this says whether anything answered at all.
    provider: str | None = None
    # What this request took, and how many it took to get here — the answering
    # one included. The retry loop's to report: a wait timed above it would
    # carry backoff this request never waited through.
    request_ms: int | None = None
    attempts: int | None = None


@dataclass(frozen=True)
class Trace:
    """What a failure still knows about itself.

    A reply carries its own count and timing; a failure has nothing to carry
    them on, and they are as much a fact about the endpoint there. Stamped on
    the exception rather than wrapped around it, so the failure keeps its type
    and every caller that catches one still catches the same thing.
    """

    attempts: int
    request_ms: int


@dataclass(frozen=True)
class Retry:
    """One transient failure, reported while it is being waited out.

    The call record already holds how many requests an answer took. What no
    record can hold is the wait itself: a run behind a per-minute cap is
    silent for as long as the backoff lasts, and silence reads as a slow
    model. So the transport says it happened and the caller decides whether
    anything prints.

    Raised to nobody and returned to nobody. A retry that succeeds is not a
    failure of the call, which is why this is a report rather than an
    exception.
    """

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
    """Absent where nothing stamped it, which is a transport that never
    retried rather than one that is wrong."""
    trace = exc.__dict__.get("trace")
    return trace if isinstance(trace, Trace) else None


class Transport(Protocol):
    """Send one prompt and come back with a `Reply`, or raise.

    Failure is raised rather than returned: `ask` records it and re-raises, so
    the caller decides whether one attempt's problem ends a run.
    """

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
