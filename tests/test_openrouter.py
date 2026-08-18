"""The transport: what leaves for OpenRouter, and what comes back as a `Reply`.

The request shape lives here rather than with the call log, which is the point
of the split — one file knows an API, the other knows a record.
"""

from dataclasses import dataclass, field
from typing import Any

import pytest

from algo_coach.calls import ROUTING, UNSENT, OpenRouter, ProviderError


@dataclass
class Message:
    content: str | None = '{"techniques": []}'
    reasoning: str | None = None


@dataclass
class Choice:
    message: Message
    finish_reason: str = "stop"


@dataclass
class Usage:
    prompt_tokens: int = 11
    completion_tokens: int = 22


@dataclass
class Completion:
    choices: list[Choice]
    usage: Usage = field(default_factory=Usage)
    provider: str | None = "Anthropic"


class Rejected(Exception):
    """What the SDK raises: the status is what a retry decision reads."""

    def __init__(self, status_code: int):
        super().__init__(f"status {status_code}")
        self.status_code = status_code


@dataclass
class FakeCompletions:
    reply: Completion
    calls: list[dict] = field(default_factory=list)
    raises: list[Exception] = field(default_factory=list)

    def create(self, **kwargs) -> Completion:
        self.calls.append(kwargs)
        if self.raises:
            raise self.raises.pop(0)
        return self.reply


@dataclass
class FakeChat:
    completions: FakeCompletions


@dataclass
class FakeClient:
    chat: FakeChat


def client(
    message: Message | None = None, raises: list[Exception] = (), **completion: Any
) -> FakeClient:
    reply = Completion([Choice(message or Message())], **completion)
    return FakeClient(FakeChat(FakeCompletions(reply, raises=list(raises))))


SCHEMA = {"type": "object", "properties": {"techniques": {"type": "array"}}}


def test_the_schema_is_sent_strict_or_it_guarantees_nothing():
    """The candidates are enforced by the response format, so a verdict cannot
    name a technique the tags do not. Without `strict` the schema is a
    suggestion and the classifier's constraint is gone."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=SCHEMA)

    (request,) = api.chat.completions.calls
    fmt = request["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["strict"] is True
    assert fmt["json_schema"]["schema"] == SCHEMA


def test_the_route_is_pinned_rather_than_left_to_the_router():
    """A provider that cannot honour the schema must never be chosen, and a
    silent second backend would make one configuration key mean two readings."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=SCHEMA)

    (request,) = api.chat.completions.calls
    assert request["extra_body"]["provider"] == {**ROUTING, "order": ["a-host"]}
    assert ROUTING["require_parameters"] is True
    assert ROUTING["allow_fallbacks"] is False


def test_the_pin_names_the_only_backend_that_may_serve():
    """`allow_fallbacks` bounds what happens after it fails; the order is what
    resolves a model id to one build in the first place."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="anthropic", schema=None)

    (request,) = api.chat.completions.calls
    routing = request["extra_body"]["provider"]
    assert routing["order"] == ["anthropic"]
    assert routing["require_parameters"] is True


def test_no_request_leaves_the_choice_to_the_router():
    """There is no unpinned path. A router picking per request answers one
    configuration key from several builds, and the readings under it could
    never be taken apart afterwards."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=None)

    (request,) = api.chat.completions.calls
    assert request["extra_body"]["provider"]["order"] == ["a-host"]


def test_an_effort_that_was_asked_for_is_sent():
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="high", pin="a-host", schema=None)

    (request,) = api.chat.completions.calls
    assert request["extra_body"]["reasoning"] == {"effort": "high"}


def test_an_unsent_effort_reaches_the_request_as_nothing():
    """A model that rejects the parameter rejects every call carrying it,
    whatever the level — `UNSENT` is how a caller says this model takes none."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort=UNSENT, pin="a-host", schema=None)

    (request,) = api.chat.completions.calls
    assert "reasoning" not in request["extra_body"]


def test_the_prompt_travels_as_two_messages_in_the_order_sent():
    api = client()

    OpenRouter(api)(
        system="sys", content="body", model="m", effort="low", pin="a-host", schema=None
    )

    (request,) = api.chat.completions.calls
    assert request["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "body"},
    ]


def test_what_came_back_is_read_into_the_terms_the_log_keeps():
    api = client(Message(content="answer", reasoning="weighing the invariant"))

    reply = OpenRouter(api)(
        system="s", content="c", model="m", effort="low", pin="a-host", schema=None
    )

    assert reply.text == "answer"
    assert reply.thinking == "weighing the invariant"
    assert reply.stop_reason == "stop"
    assert (reply.input_tokens, reply.output_tokens) == (11, 22)
    assert reply.provider == "Anthropic"


def test_a_model_that_shows_no_reasoning_leaves_it_empty():
    """A fact about the model rather than a gap in the record."""
    api = client(Message(reasoning=None))

    reply = OpenRouter(api)(
        system="s", content="c", model="m", effort="low", pin="a-host", schema=None
    )

    assert reply.thinking is None


def test_an_answer_with_no_content_is_no_verdict():
    """`ask` records it as the failure it is; the transport only reports that
    nothing came back."""
    api = client(Message(content=""), provider="Some Host")

    reply = OpenRouter(api)(
        system="s", content="c", model="m", effort="low", pin="a-host", schema=None
    )

    assert reply.text is None
    assert reply.provider == "Some Host"


def test_a_gateway_failure_is_waited_out_like_a_cap(monkeypatch):
    """A 200 carrying a 502 is the router saying the provider it picked broke.
    Reported upward, three of them in a row abort a backlog run over something
    that fixes itself."""
    slept: list[float] = []
    monkeypatch.setattr("algo_coach.calls.openrouter.time.sleep", slept.append)
    api = client()
    broken = Completion([], provider=None)
    broken.error = {"message": "ext_proc failed", "code": 502}
    replies = [broken, api.chat.completions.reply]
    api.chat.completions.create = lambda **kw: (
        api.chat.completions.calls.append(kw) or replies.pop(0)
    )

    reply = OpenRouter(api)(
        system="s", content="c", model="m", effort="low", pin="a-host", schema=None
    )

    assert reply.text == '{"techniques": []}'
    assert slept == [5.0]


def test_a_choice_that_stopped_on_an_error_is_not_an_empty_verdict(monkeypatch):
    """Read as one it would be recorded as the model declining — a claim about
    the model rather than about the gateway between us and it."""
    monkeypatch.setattr("algo_coach.calls.openrouter.time.sleep", lambda _: None)
    api = client(Message(content=None))
    api.chat.completions.reply.choices[0].finish_reason = "error"
    api.chat.completions.reply.error = {"message": "upstream died", "code": 503}

    with pytest.raises(ProviderError, match="upstream died"):
        OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=None)


def test_a_rejected_schema_is_not_waited_out(monkeypatch):
    """Asking again answers the same way: the configuration is wrong, and the
    abort count is what should notice."""
    slept: list[float] = []
    monkeypatch.setattr("algo_coach.calls.openrouter.time.sleep", slept.append)
    api = client()
    broken = Completion([], provider=None)
    broken.error = {"message": "json_schema not supported", "code": 405}
    api.chat.completions.reply = broken

    with pytest.raises(ProviderError, match="json_schema"):
        OpenRouter(api)(
            system="s", content="c", model="m", effort="low", pin="a-host", schema=SCHEMA
        )

    assert slept == []


def test_a_rate_limit_is_waited_out_rather_than_reported(monkeypatch):
    """A per-minute cap is a fact about the endpoint. Reported upward it would
    spend a run's abort count on something that fixes itself."""
    slept: list[float] = []
    monkeypatch.setattr("algo_coach.calls.openrouter.time.sleep", slept.append)
    api = client(raises=[Rejected(429), Rejected(429)])

    reply = OpenRouter(api)(
        system="s", content="c", model="m", effort="low", pin="a-host", schema=None
    )

    assert reply.text == '{"techniques": []}'
    assert len(api.chat.completions.calls) == 3
    assert slept == [5.0, 15.0]


def test_every_other_failure_is_raised_on_the_first_try(monkeypatch):
    """A bad key and a rejected schema do not improve by being asked again."""
    slept: list[float] = []
    monkeypatch.setattr("algo_coach.calls.openrouter.time.sleep", slept.append)
    api = client(raises=[Rejected(401)])

    with pytest.raises(Rejected):
        OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=None)

    assert len(api.chat.completions.calls) == 1
    assert slept == []


def test_a_cap_that_never_lifts_is_reported_in_the_end(monkeypatch):
    """The waits cover a minute between them; past that the endpoint is not
    rate limiting, it is refusing."""
    monkeypatch.setattr("algo_coach.calls.openrouter.time.sleep", lambda _: None)
    api = client(raises=[Rejected(429)] * 5)

    with pytest.raises(Rejected):
        OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=None)

    assert len(api.chat.completions.calls) == 5


def test_an_answer_with_no_choices_names_whose_fault_it_was():
    """A router reports a failed provider as a 200 carrying an error and no
    choices. Subscripting that is a TypeError with nothing in it; the body is
    the only place that says what happened."""
    api = client()
    api.chat.completions.reply = Completion([], provider=None)
    api.chat.completions.reply.error = {"message": "upstream timed out"}

    with pytest.raises(ProviderError, match="upstream timed out"):
        OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=None)


def test_no_choices_and_no_error_still_says_something():
    api = client()
    api.chat.completions.reply = Completion([], provider=None)

    with pytest.raises(ProviderError, match="no choices returned"):
        OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", schema=None)


def test_the_temperature_is_sent_as_the_api_s_own_parameter():
    """Top level, not inside `provider`: it is an OpenAI-shaped field, and one
    buried in the routing block would be read as routing and dropped."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", pin="a-host", temperature=0.0)

    (request,) = api.chat.completions.calls
    assert request["temperature"] == 0.0
    assert "temperature" not in request["extra_body"]


def test_no_temperature_sends_none_at_all():
    """The provider's own default, which is what every stored reading was taken
    at — a configuration in its own right, and not one to be forged by sending
    a number that happens to match."""
    api = client()

    OpenRouter(api)(
        system="s", content="c", model="m", effort="low", pin="a-host", temperature=None
    )

    (request,) = api.chat.completions.calls
    assert "temperature" not in request
