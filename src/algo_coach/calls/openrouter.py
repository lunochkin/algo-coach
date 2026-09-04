"""The one transport: chat completions, spoken to OpenRouter. Never fall back
to Anthropic's own compatibility layer: it ignores `response_format`, `strict`
and `reasoning_effort`, so the schema goes unenforced and the effort
dropped."""

import time
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from algo_coach.calls.transport import MAX_TOKENS, ProviderError, Reply, Retry, Trace, stamp

BASE_URL = "https://openrouter.ai/api/v1"

# `require_parameters` drops a provider that cannot honour what was sent, and
# `allow_fallbacks` off fails the request rather than serving it elsewhere.
ROUTING = {"require_parameters": True, "allow_fallbacks": False}

# The effort recorded for a model asked for none; some reject the parameter.
UNSENT = "default"

# The name reaches the model, so it says what the object is.
FORMAT = "verdict"

BACKOFF = (5.0, 15.0, 30.0, 60.0)

# Worth asking again: too many requests, and the gateway failing between the
# router and whoever it picked. A rejected schema or an unset key would not be.
TRANSIENT = frozenset({429, 500, 502, 503, 504})

# The router answering that nothing serves this model right now. Its list moves
# under a pinned request, so this reports state rather than a rejected request.
# A model id that does not exist says the same, and pays the one retry.
UNROUTED = "no endpoints"


# The same failure arrives as an SDK status or as a code inside a 200,
# depending on where it happened.
def status(exc: Exception) -> int | None:
    return getattr(exc, "status_code", None) or getattr(exc, "code", None)


def transient(exc: Exception) -> bool:
    return status(exc) in TRANSIENT


def unrouted(exc: Exception) -> bool:
    return status(exc) == 404 and UNROUTED in str(exc).lower()


def failure(error: Any) -> tuple[str, int | None]:
    """A provider's error body as a message and, where it gave one, a code."""
    if isinstance(error, dict):
        return str(error.get("message") or error), error.get("code")
    return str(error or "no choices returned"), None


def extra(obj: Any, name: str) -> Any:
    """A field the SDK does not model: OpenRouter's own additions arrive beside
    the typed ones."""
    value = getattr(obj, name, None)
    if value is None:
        value = (getattr(obj, "model_extra", None) or {}).get(name)
    return value or None


@dataclass(frozen=True)
class OpenRouter:
    """A transport over an OpenAI-shaped client pointed at OpenRouter."""

    client: Any
    # Called on the requesting thread as a transient failure is waited out.
    on_retry: Callable[[Retry], None] | None = None

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
        max_tokens: int = MAX_TOKENS,
    ) -> Reply:
        # `order` is what makes a model id resolve to one build; without it the
        # router picks among the providers carrying the model.
        body: dict[str, Any] = {"provider": {**ROUTING, "order": [pin]}}
        if effort != UNSENT:
            body["reasoning"] = {"effort": effort}

        request: dict[str, Any] = {}
        # Top level, not inside `provider`: it is the API's own parameter.
        # Omitted rather than defaulted, so a provider's own choice stays
        # visible.
        if temperature is not None:
            request["temperature"] = temperature
        if schema is not None:
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": FORMAT, "strict": True, "schema": schema},
            }

        return self.send(
            pin=pin,
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            extra_body=body,
            **request,
        )

    def send(self, *, pin: str, **request: Any) -> Reply:
        """One reading, repeated while the endpoint answers with a reason to
        ask again, and raised on the first try otherwise."""
        rerouted = False  # the one retry an unrouted 404 is given
        for tries, pause in enumerate(BACKOFF, start=1):
            try:
                return self.once(tries, **request)
            except Exception as exc:
                if unrouted(exc) and not rerouted:
                    # the shortest wait: what this asks is whether the router's
                    # list moved, not whether a cap window passed
                    rerouted, pause, of = True, BACKOFF[0], tries + 1
                elif transient(exc):
                    of = len(BACKOFF) + 1
                else:
                    raise
                self.held(exc, pin=pin, model=request["model"], tries=tries, of=of, pause=pause)
                time.sleep(pause)
        return self.once(len(BACKOFF) + 1, **request)

    def held(
        self, exc: Exception, *, pin: str, model: str, tries: int, of: int, pause: float
    ) -> None:
        """Report one wait, before the sleep it is about."""
        if self.on_retry is not None:
            self.on_retry(
                Retry(
                    status=status(exc),
                    model=model,
                    pin=pin,
                    tries=tries,
                    of=of,
                    pause=pause,
                    reason=str(exc),
                )
            )

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
            # provider it chose failed. The body is the only place that says
            # so.
            raise ProviderError(*failure(extra(response, "error")))

        choice = choices[0]
        if choice.finish_reason == "error" and not choice.message.content:
            # The same failure with a choice around it. Read as an empty
            # verdict it would record the gateway's fault as the model
            # declining.
            raise ProviderError(*failure(extra(response, "error") or "stopped on error"))

        usage = getattr(response, "usage", None)
        return Reply(
            text=choice.message.content or None,
            thinking=extra(choice.message, "reasoning"),
            stop_reason=choice.finish_reason,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
            cost=extra(usage, "cost") if usage is not None else None,
            reasoning_tokens=reasoning(usage),
            provider=extra(response, "provider"),
        )


def reasoning(usage: Any) -> int | None:
    """How much of the completion was spent thinking, where the router said it.
    Absent rather than zero: thinking nothing and not reporting a split
    differ."""
    details = getattr(usage, "completion_tokens_details", None) if usage is not None else None
    if details is None:
        return None
    value = getattr(details, "reasoning_tokens", None)
    if value is None and isinstance(details, dict):
        value = details.get("reasoning_tokens")
    return value


def since(started: float) -> int:
    return round((time.monotonic() - started) * 1000)
