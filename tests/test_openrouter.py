"""The transport: what leaves for OpenRouter, and what comes back as a `Reply`.

The request shape lives here rather than with the call log, which is the point
of the split — one file knows an API, the other knows a record.
"""

from dataclasses import dataclass, field
from typing import Any

from algo_coach.calls import ROUTING, UNSENT, OpenRouter


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


@dataclass
class FakeCompletions:
    reply: Completion
    calls: list[dict] = field(default_factory=list)

    def create(self, **kwargs) -> Completion:
        self.calls.append(kwargs)
        return self.reply


@dataclass
class FakeChat:
    completions: FakeCompletions


@dataclass
class FakeClient:
    chat: FakeChat


def client(message: Message | None = None, **completion: Any) -> FakeClient:
    reply = Completion([Choice(message or Message())], **completion)
    return FakeClient(FakeChat(FakeCompletions(reply)))


SCHEMA = {"type": "object", "properties": {"techniques": {"type": "array"}}}


def test_the_schema_is_sent_strict_or_it_guarantees_nothing():
    """The candidates are enforced by the response format, so a verdict cannot
    name a technique the tags do not. Without `strict` the schema is a
    suggestion and the classifier's constraint is gone."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", schema=SCHEMA)

    (request,) = api.chat.completions.calls
    fmt = request["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["json_schema"]["strict"] is True
    assert fmt["json_schema"]["schema"] == SCHEMA


def test_the_route_is_pinned_rather_than_left_to_the_router():
    """A provider that cannot honour the schema must never be chosen, and a
    silent second backend would make one configuration key mean two readings."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", schema=SCHEMA)

    (request,) = api.chat.completions.calls
    assert request["extra_body"]["provider"] == ROUTING
    assert ROUTING["require_parameters"] is True
    assert ROUTING["allow_fallbacks"] is False


def test_a_pinned_provider_names_the_only_backend_that_may_serve():
    """`allow_fallbacks` bounds what happens after one fails; the first choice
    among those carrying the model is the router's until an order names one."""
    api = client()

    OpenRouter(api)(
        system="s", content="c", model="m", effort="low", provider="anthropic", schema=None
    )

    (request,) = api.chat.completions.calls
    routing = request["extra_body"]["provider"]
    assert routing["order"] == ["anthropic"]
    assert routing["require_parameters"] is True


def test_an_unpinned_provider_leaves_the_choice_to_the_router():
    """Which is legal, and why the call records who answered rather than who
    was asked for."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="low", schema=None)

    (request,) = api.chat.completions.calls
    assert "order" not in request["extra_body"]["provider"]


def test_an_effort_that_was_asked_for_is_sent():
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort="high", schema=None)

    (request,) = api.chat.completions.calls
    assert request["extra_body"]["reasoning"] == {"effort": "high"}


def test_an_unsent_effort_reaches_the_request_as_nothing():
    """A model that rejects the parameter rejects every call carrying it,
    whatever the level — `UNSENT` is how a caller says this model takes none."""
    api = client()

    OpenRouter(api)(system="s", content="c", model="m", effort=UNSENT, schema=None)

    (request,) = api.chat.completions.calls
    assert "reasoning" not in request["extra_body"]


def test_the_prompt_travels_as_two_messages_in_the_order_sent():
    api = client()

    OpenRouter(api)(system="sys", content="body", model="m", effort="low", schema=None)

    (request,) = api.chat.completions.calls
    assert request["messages"] == [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "body"},
    ]


def test_what_came_back_is_read_into_the_terms_the_log_keeps():
    api = client(Message(content="answer", reasoning="weighing the invariant"))

    reply = OpenRouter(api)(system="s", content="c", model="m", effort="low", schema=None)

    assert reply.text == "answer"
    assert reply.thinking == "weighing the invariant"
    assert reply.stop_reason == "stop"
    assert (reply.input_tokens, reply.output_tokens) == (11, 22)
    assert reply.provider == "Anthropic"


def test_a_model_that_shows_no_reasoning_leaves_it_empty():
    """A fact about the model rather than a gap in the record."""
    api = client(Message(reasoning=None))

    reply = OpenRouter(api)(system="s", content="c", model="m", effort="low", schema=None)

    assert reply.thinking is None


def test_an_answer_with_no_content_is_no_verdict():
    """`ask` records it as the failure it is; the transport only reports that
    nothing came back."""
    api = client(Message(content=""), provider="Some Host")

    reply = OpenRouter(api)(system="s", content="c", model="m", effort="low", schema=None)

    assert reply.text is None
    assert reply.provider == "Some Host"
