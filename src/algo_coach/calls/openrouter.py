"""The one transport: chat completions, spoken to OpenRouter.

Every model is reached through one endpoint and one request shape, so adding a
model is a string and adding a provider is a base URL. An outage falls back to
another endpoint of the same shape — never to Anthropic's own compatibility
layer, which ignores `response_format`, `strict` and `reasoning_effort` and so
answers with the schema unenforced and the effort dropped.
"""

import time
from dataclasses import dataclass, replace
from typing import Any

from algo_coach.calls.transport import ProviderError, Reply, Trace, stamp

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

# How long to hold off before asking again, and how many times. Absorbed here
# rather than reported upward: a cap and a gateway failure are facts about the
# endpoint, and a run that abandons a backlog over one is spending the wrong
# thing — the abort exists to catch a broken configuration, which neither is.
# The waits cover a minute between them, since that is the window a per-minute
# cap is stated in; the endpoint's own reset time is not read, because where it
# is carried varies by provider and a wrong parse would sleep for hours.
BACKOFF = (5.0, 15.0, 30.0, 60.0)

# Worth asking again: too many requests, and the gateway failing between the
# router and whoever it picked. Everything else is answered the same way twice —
# a rejected schema, an unset key, a model that does not exist.
TRANSIENT = frozenset({429, 500, 502, 503, 504})


def transient(exc: Exception) -> bool:
    """Whether asking again is worth anything.

    A status from the SDK, or the code a router carried inside a 200 — the
    same failure reaches us both ways depending on where it happened.
    """
    code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return code in TRANSIENT


def failure(error: Any) -> tuple[str, int | None]:
    """A provider's error body as a message and, where it gave one, a code."""
    if isinstance(error, dict):
        return str(error.get("message") or error), error.get("code")
    return str(error or "no choices returned"), None


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
        pin: str,
        temperature: float | None = None,
        schema: dict[str, Any] | None = None,
        max_tokens: int = 16000,
    ) -> Reply:
        # `allow_fallbacks` bounds what happens after a provider fails; the
        # first choice among those carrying the model is still the router's
        # until an order names one. Both together are what make a model id
        # resolve to one backend.
        # `allow_fallbacks` bounds what happens after the pinned endpoint
        # fails; the order is what makes a model id resolve to one build in
        # the first place. Both together, or a reading names a model and not
        # a reader.
        body: dict[str, Any] = {"provider": {**ROUTING, "order": [pin]}}
        if effort != UNSENT:
            body["reasoning"] = {"effort": effort}

        request: dict[str, Any] = {}
        # Top level, not inside `provider`: it is the API's own parameter, and
        # one sent as routing would be read as routing. Omitted rather than
        # defaulted, so the provider's own choice stays distinguishable from a
        # number we picked that happens to match it.
        if temperature is not None:
            request["temperature"] = temperature
        if schema is not None:
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": FORMAT, "strict": True, "schema": schema},
            }

        return self.send(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            extra_body=body,
            **request,
        )

    def send(self, **request: Any) -> Reply:
        """One reading, held and repeated while the endpoint answers with a
        reason to ask again.

        Every other failure is raised on the first try: a bad key and a
        rejected schema do not improve by being asked again, and a run that
        retried them would burn its abort count slowly instead of at once.

        The count and the last request's time ride back with the outcome,
        whichever it is: a caller sees one call however many requests it took,
        and only this loop knows how many that was.
        """
        for tries, pause in enumerate(BACKOFF, start=1):
            try:
                return self.once(tries, **request)
            except Exception as exc:
                if not transient(exc):
                    raise
                time.sleep(pause)
        return self.once(len(BACKOFF) + 1, **request)

    def once(self, tries: int, **request: Any) -> Reply:
        """One request, timed and counted whether it answers or fails."""
        started = time.monotonic()
        try:
            return replace(self.attempt(**request), attempts=tries, request_ms=since(started))
        except Exception as exc:
            stamp(exc, Trace(attempts=tries, request_ms=since(started)))
            raise

    def attempt(self, **request: Any) -> Reply:
        """One request, read into the terms the call log keeps."""
        response = self.client.chat.completions.create(**request)

        choices = getattr(response, "choices", None)
        if not choices:
            # A 200 with an error and no choices: the router reporting that the
            # provider it chose failed. The body says whose and why, and it is
            # the only place that says it.
            raise ProviderError(*failure(extra(response, "error")))

        choice = choices[0]
        if choice.finish_reason == "error" and not choice.message.content:
            # The same failure, arriving with a choice around it. Read as an
            # empty verdict it would be recorded as the model declining, which
            # is a claim about the model rather than about the gateway.
            raise ProviderError(*failure(extra(response, "error") or "stopped on error"))

        usage = getattr(response, "usage", None)
        return Reply(
            text=choice.message.content or None,
            thinking=extra(choice.message, "reasoning"),
            stop_reason=choice.finish_reason,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            provider=extra(response, "provider"),
        )


def since(started: float) -> int:
    """Milliseconds, since nothing reads a request's timing more finely."""
    return round((time.monotonic() - started) * 1000)
