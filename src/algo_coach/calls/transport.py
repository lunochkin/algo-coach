"""What a transport returns, and what one is.

The shape a provider answers in is the provider's; what the log records is
ours. `Reply` is the line between them — a transport turns one API's response
into this, and nothing above it ever sees a content block or a choice.

One shape at a time, by rule. Two provider shapes maintained by hand is what
invites a library to reconcile them, and a library that reconciles them can
downgrade a schema into a prompt where the record cannot show it happened.
"""

from dataclasses import dataclass
from typing import Any, Protocol


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
    # Who actually served it — the name the router reports, which is the
    # company rather than the endpoint. The build asked for is the request's
    # own `pin`; this says whether anything answered at all.
    provider: str | None = None


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
