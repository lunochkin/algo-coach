"""The one transport: chat completions, spoken to OpenRouter.

Every model is reached through one endpoint and one request shape, so adding a
model is a string and adding a provider is a base URL. An outage falls back to
another endpoint of the same shape — never to Anthropic's own compatibility
layer, which ignores `response_format`, `strict` and `reasoning_effort` and so
answers with the schema unenforced and the effort dropped.
"""

import time
from dataclasses import dataclass
from typing import Any

from algo_coach.calls.transport import ProviderError, Reply

BASE_URL = "https://openrouter.ai/api/v1"

# What every request constrains, whatever it asks for. `require_parameters`
# drops any provider that cannot honour what was sent — without it a provider
# lacking structured outputs still answers, and the schema stops being the
# thing that keeps a verdict inside the candidates. `allow_fallbacks` off means
# a request fails rather than being served by a second backend after the first
# one did not answer.
ROUTING = {"require_parameters": True, "allow_fallbacks": False}

# The effort of a model that is asked for none — some reject the parameter
# outright. A named level rather than an absent field, since a reading whose
# configuration is partly unknown compares with nothing.
UNSENT = "default"

# The schema's name reaches the model, so it says what the object is rather
# than that it is an object.
FORMAT = "verdict"

# How long to hold off after a rate limit, and how many times. Absorbed here
# rather than reported upward: a per-minute cap is a fact about the endpoint,
# and a run that abandons a backlog over one is spending the wrong thing. The
# waits cover a minute between them, since that is the window such caps are
# usually stated in — the endpoint's own reset time is not read, because where
# it is carried varies by provider and a wrong parse would sleep for hours.
BACKOFF = (5.0, 15.0, 30.0, 60.0)
RATE_LIMITED = 429


def extra(obj: Any, name: str) -> Any:
    """A field the SDK does not model. Reasoning and the serving provider are
    OpenRouter's own additions, so they arrive beside the typed ones."""
    value = getattr(obj, name, None)
    if value is None:
        value = (getattr(obj, "model_extra", None) or {}).get(name)
    return value or None


@dataclass(frozen=True)
class OpenRouter:
    """A transport over an OpenAI-shaped client pointed at OpenRouter."""

    client: Any

    def __call__(
        self,
        *,
        system: str,
        content: str,
        model: str,
        effort: str,
        provider: str | None = None,
        schema: dict[str, Any] | None = None,
        max_tokens: int = 16000,
    ) -> Reply:
        # `allow_fallbacks` bounds what happens after a provider fails; the
        # first choice among those carrying the model is still the router's
        # until an order names one. Both together are what make a model id
        # resolve to one backend.
        routing = dict(ROUTING) if provider is None else {**ROUTING, "order": [provider]}
        body: dict[str, Any] = {"provider": routing}
        if effort != UNSENT:
            body["reasoning"] = {"effort": effort}

        request: dict[str, Any] = {}
        if schema is not None:
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": FORMAT, "strict": True, "schema": schema},
            }

        response = self.send(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            extra_body=body,
            **request,
        )
        choices = getattr(response, "choices", None)
        if not choices:
            # A 200 with an error and no choices: the router reporting that the
            # provider it chose failed. The body says whose and why, and it is
            # the only place that says it.
            raise ProviderError(str(extra(response, "error") or "no choices returned"))

        choice = choices[0]
        usage = getattr(response, "usage", None)
        return Reply(
            text=choice.message.content or None,
            thinking=extra(choice.message, "reasoning"),
            stop_reason=choice.finish_reason,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            provider=extra(response, "provider"),
        )

    def send(self, **request: Any) -> Any:
        """One request, held and repeated while the endpoint says too many.

        Every other failure is raised on the first try: a bad key and a
        rejected schema do not improve by being asked again, and a run that
        retried them would burn its abort count slowly instead of at once.
        """
        for pause in BACKOFF:
            try:
                return self.client.chat.completions.create(**request)
            except Exception as exc:
                if getattr(exc, "status_code", None) != RATE_LIMITED:
                    raise
                time.sleep(pause)
        return self.client.chat.completions.create(**request)
