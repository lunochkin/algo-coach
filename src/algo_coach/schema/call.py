from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class Call(BaseModel):
    id: str
    created_at: datetime
    model: str
    effort: str
    prompt: str = Field(min_length=1)  # inline: a file plus a log line can half-succeed
    prompt_hash: str = Field(min_length=1)  # not unique; a retry and re-sampling both repeat it
    response: str | None = None
    error: str | None = None
    thinking: str | None = None  # absent where the model judged it needed none
    stop_reason: str | None = None
    temperature: float | None = None  # absent is the provider's default, which moves
    pin: str | None = None  # the endpoint, named to the quantization
    provider: str | None = None  # who served it, as the router reports: a company
    input_tokens: int | None = None
    output_tokens: int | None = None
    # Not reliably a part of `output_tokens`: some providers count it inside
    # the completion and some beside it, so the two are read against each
    # other rather than subtracted. Zero and absent are different facts.
    reasoning_tokens: int | None = None
    cost: float | None = None  # as the router charged then, not a rate applied later
    elapsed_ms: int | None = None  # what the caller waited, over `attempts` requests
    attempts: int | None = None
    request_ms: int | None = None  # the last request alone: the one that answered or failed

    @model_validator(mode="after")
    def _answered_or_failed(self) -> Call:
        """Rejects a call carrying both a response and an error, or neither."""
        if (self.response is None) == (self.error is None):
            raise ValueError("a call carries either a response or an error")
        return self
