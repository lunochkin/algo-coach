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
    # Who actually served it. A model id stops answering that the moment
    # anything routes, and a reading whose configuration is partly unknown
    # compares with nothing.
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
        provider: str | None,
        schema: dict[str, Any] | None,
        max_tokens: int,
    ) -> Reply: ...
