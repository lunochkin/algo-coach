"""The call log: what was asked of a model and what came back.

Domain-free on purpose — nothing here knows what a technique is, which is what
lets a second consumer read the log without being taught anything.
"""

from dataclasses import dataclass, field
from hashlib import sha256

import pytest

from algo_coach.calls import THINKING, UNSENT, CallLog, ask, payload, prompt_hash
from algo_coach.mint import call as mint_call
from algo_coach.schema import Call


@dataclass
class Block:
    text: str = ""
    thinking: str = ""
    type: str = "text"


@dataclass
class Usage:
    input_tokens: int = 11
    output_tokens: int = 22


@dataclass
class Response:
    content: list[Block]
    stop_reason: str = "end_turn"
    usage: Usage = field(default_factory=Usage)


@dataclass
class FakeMessages:
    reply: Response | None = None
    error: Exception | None = None
    calls: list[dict] = field(default_factory=list)

    def create(self, **kwargs) -> Response:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.reply


@dataclass
class FakeClient:
    messages: FakeMessages


def answering(text: str = '{"ok": true}', thinking: str = "") -> FakeClient:
    blocks = [Block(text=text)]
    if thinking:
        blocks.insert(0, Block(thinking=thinking, type="thinking"))
    return FakeClient(FakeMessages(Response(blocks)))


def test_the_stored_prompt_digests_to_the_hash_beside_it(tmp_path):
    """The point of keeping the text: a record that cannot be checked against
    its own key is a claim about what was sent rather than the thing itself."""
    log = CallLog(tmp_path)

    ask(answering(), log, system="sys", content="body", model="m", effort="low")

    (stored,) = log.all()
    assert sha256(stored.prompt.encode()).hexdigest()[: len(stored.prompt_hash)] == (
        stored.prompt_hash
    )


def test_the_prompt_is_both_halves_in_the_order_sent(tmp_path):
    log = CallLog(tmp_path)

    ask(answering(), log, system="sys", content="body", model="m", effort="low")

    (stored,) = log.all()
    assert "sys" in stored.prompt and "body" in stored.prompt
    assert stored.prompt == payload("sys", "body")


def test_what_came_back_is_recorded_beside_what_it_cost(tmp_path):
    log = CallLog(tmp_path)

    call, text = ask(
        answering('{"techniques": []}', thinking="weighing the invariant"),
        log,
        system="sys",
        content="body",
        model="m",
        effort="low",
    )

    assert text == '{"techniques": []}'
    (stored,) = log.all()
    assert stored.response == '{"techniques": []}'
    assert stored.thinking == "weighing the invariant"
    assert (stored.input_tokens, stored.output_tokens) == (11, 22)
    assert stored.stop_reason == "end_turn"
    assert stored.id == call.id


def test_a_failure_is_recorded_and_then_raised(tmp_path):
    """A run that broke at two in the morning is readable afterwards, rather
    than a counter that printed once and vanished."""
    log = CallLog(tmp_path)
    client = FakeClient(FakeMessages(error=RuntimeError("rate limited")))

    with pytest.raises(RuntimeError):
        ask(client, log, system="sys", content="body", model="m", effort="low")

    (stored,) = log.all()
    assert stored.error == "RuntimeError: rate limited"
    assert stored.response is None


def test_a_reply_with_no_text_is_a_failure_not_an_empty_reading(tmp_path):
    """A refusal and an answer cut short both land here. Recording it as a
    response would say the model answered nothing on purpose."""
    log = CallLog(tmp_path)
    client = FakeClient(FakeMessages(Response([], stop_reason="refusal")))

    call, text = ask(client, log, system="sys", content="body", model="m", effort="low")

    assert text is None
    assert "refusal" in call.error


def test_an_unsent_effort_leaves_thinking_off_the_request_too(tmp_path):
    """They arrived together, so a model old enough to reject the effort
    parameter rejects adaptive thinking as well — `UNSENT` says both in one
    word, and sending either to such a model fails every call identically."""
    log = CallLog(tmp_path)
    client = answering()

    ask(client, log, system="sys", content="body", model="m", effort=UNSENT)

    (request,) = client.messages.calls
    assert "effort" not in request["output_config"]
    assert "thinking" not in request


def test_an_effort_that_was_asked_for_brings_thinking_with_it(tmp_path):
    log = CallLog(tmp_path)
    client = answering()

    ask(client, log, system="sys", content="body", model="m", effort="low")

    (request,) = client.messages.calls
    assert request["output_config"]["effort"] == "low"
    assert request["thinking"] == THINKING


def test_the_same_prompt_may_be_called_more_than_once(tmp_path):
    """Sampling one prompt on purpose, and a retry after a rate limit, both
    repeat a hash — so nothing may assume one call per hash."""
    log = CallLog(tmp_path)

    ask(answering(), log, system="sys", content="body", model="m", effort="low")
    ask(answering(), log, system="sys", content="body", model="m", effort="low")

    first, second = log.all()
    assert first.prompt_hash == second.prompt_hash
    assert first.id != second.id


def test_the_hash_ignores_what_the_hash_cannot_see(tmp_path):
    """The output schema is built from the candidates, which are already in the
    content — so hashing it would vary with nothing new."""
    assert prompt_hash("sys", "body") == prompt_hash("sys", "body")
    assert prompt_hash("sys", "body") != prompt_hash("sys", "other")
    assert prompt_hash("sys", "body") != prompt_hash("other", "body")


def test_a_call_carries_an_outcome_or_it_is_not_a_call():
    with pytest.raises(ValueError, match="response or an error"):
        mint_call(model="m", effort="low", prompt="p", prompt_hash="h")
    with pytest.raises(ValueError, match="response or an error"):
        mint_call(model="m", effort="low", prompt="p", prompt_hash="h", response="r", error="e")


def test_an_empty_log_reads_as_nothing(tmp_path):
    assert CallLog(tmp_path).all() == []


def test_the_log_round_trips(tmp_path):
    log = CallLog(tmp_path)
    call = mint_call(model="m", effort="low", prompt="p", prompt_hash="h", response="r")

    log.append(call)

    assert log.all() == [call]
    assert isinstance(log.all()[0], Call)
