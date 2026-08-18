from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class Call(BaseModel):
    """One request to a model and what came back.

    Deliberately knows nothing about what the answer was for: no attempt, no
    techniques, no vocabulary. A domain record cites a call by `id` and reads
    its own meaning into the response; this record only says what was asked,
    of whom, and what returned. That is what lets a second domain reuse the
    log without teaching it anything.

    Kept for what a claim cannot hold: the tokens a run cost, the reasoning
    behind a verdict, and the calls that produced no claim at all — a decline
    names no candidate and a failure names nothing, and both were counters
    that printed once and vanished.

    `prompt_hash` is not unique. A call retried after a rate limit repeats it,
    and sampling one prompt several times repeats it on purpose — so a reader
    looking one up must say which it wants rather than assume there is one.
    """

    id: str  # engine-minted
    created_at: datetime
    model: str
    effort: str
    # The exact payload, and its digest. Stored beside each other rather than
    # deduplicated into a store of their own: one append cannot half-succeed,
    # and a call naming a prompt that is not there is the gap this record
    # exists to close.
    prompt: str = Field(min_length=1)
    prompt_hash: str = Field(min_length=1)
    # Whichever happened. A call returns an answer or it fails.
    response: str | None = None
    error: str | None = None
    # The reasoning behind the answer, where the reading produced any.
    # Absent on a failure, and on a question the model judged needed no
    # thought — a fact about that reading rather than a gap in the record.
    thinking: str | None = None
    stop_reason: str | None = None
    # What the answer was sampled at. `None` is the provider's own default,
    # which moves without notice — so it is left absent rather than guessed at,
    # and a reading taken at it is its own arm rather than a gap in the log.
    temperature: float | None = None
    # The endpoint the request was pinned to, named to the quantization: an
    # fp4 build and a bf16 one are two readers, so this is what says which
    # answered. Optional only for the calls made before pinning was required.
    pin: str | None = None
    # Who actually served it, as the router reports — a company name rather
    # than an endpoint, so it confirms the pin held without identifying the
    # build on its own.
    provider: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None

    @model_validator(mode="after")
    def _answered_or_failed(self) -> Call:
        """One or the other, never both and never neither: a call that records
        no outcome is a line saying only that money may have been spent."""
        if (self.response is None) == (self.error is None):
            raise ValueError("a call carries either a response or an error")
        return self
