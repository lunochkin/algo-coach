from dataclasses import dataclass, field, replace
from hashlib import sha256
from importlib import import_module

import pytest

from algo_coach.calls import CallLog, Reply, Trace, ask, payload, prompt_hash, recorded, stamp
from algo_coach.schema import Call, Configuration

CONFIGURATION = Configuration(model="m", effort="low", pin="a-host")

ASK = import_module("algo_coach.calls.ask")


@dataclass
class FakeTransport:
    """One scripted reply, or one failure. What was asked of it is recorded,
    since a call's own record is what these tests read back."""

    reply: Reply | None = None
    error: Exception | None = None
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.reply


def answering(text: str = '{"ok": true}', thinking: str | None = None) -> FakeTransport:
    return FakeTransport(
        Reply(
            text=text,
            thinking=thinking,
            stop_reason="stop",
            input_tokens=11,
            output_tokens=22,
            provider="a-provider",
        )
    )


def test_the_stored_prompt_digests_to_the_hash_beside_it(tmp_path):
    """The point of keeping the text: a record that cannot be checked against
    its own key is a claim about what was sent rather than the thing itself."""
    log = CallLog(tmp_path)

    ask(
        answering(),
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION,
    )

    (stored,) = log.all()
    assert sha256(stored.prompt.encode()).hexdigest()[: len(stored.prompt_hash)] == (
        stored.prompt_hash
    )


def test_the_prompt_is_both_halves_in_the_order_sent(tmp_path):
    log = CallLog(tmp_path)

    ask(
        answering(),
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION,
    )

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
        configuration=CONFIGURATION,
    )

    assert text == '{"techniques": []}'
    (stored,) = log.all()
    assert stored.response == '{"techniques": []}'
    assert stored.thinking == "weighing the invariant"
    assert (stored.input_tokens, stored.output_tokens) == (11, 22)
    assert stored.stop_reason == "stop"
    assert stored.provider == "a-provider"
    assert stored.id == call.id


def test_a_failure_is_recorded_and_then_raised(tmp_path):
    """A run that broke at two in the morning is readable afterwards, rather
    than a counter that printed once and vanished."""
    log = CallLog(tmp_path)
    transport = FakeTransport(error=RuntimeError("rate limited"))

    with pytest.raises(RuntimeError):
        ask(
            transport,
            log,
            system="sys",
            content="body",
            configuration=CONFIGURATION,
        )

    (stored,) = log.all()
    assert stored.error == "RuntimeError: rate limited"
    assert stored.response is None


def test_a_reply_with_no_text_is_a_failure_not_an_empty_reading(tmp_path):
    """A refusal and an answer cut short both land here. Recording it as a
    response would say the model answered nothing on purpose."""
    log = CallLog(tmp_path)
    transport = FakeTransport(Reply(text=None, stop_reason="content_filter"))

    call, text = ask(
        transport,
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION,
    )

    assert text is None
    assert "content_filter" in call.error


def test_the_same_prompt_may_be_called_more_than_once(tmp_path):
    """Sampling one prompt on purpose, and a retry after a rate limit, both
    repeat a hash — so nothing may assume one call per hash."""
    log = CallLog(tmp_path)

    ask(
        answering(),
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION,
    )
    ask(
        answering(),
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION,
    )

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
        recorded(model="m", effort="low", prompt="p", prompt_hash="h")
    with pytest.raises(ValueError, match="response or an error"):
        recorded(model="m", effort="low", prompt="p", prompt_hash="h", response="r", error="e")


def test_an_empty_log_reads_as_nothing(tmp_path):
    assert CallLog(tmp_path).all() == []


def test_the_log_round_trips(tmp_path):
    log = CallLog(tmp_path)
    call = recorded(model="m", effort="low", prompt="p", prompt_hash="h", response="r")

    log.append(call)

    assert log.all() == [call]
    assert isinstance(log.all()[0], Call)


def test_the_call_records_what_it_was_sampled_at(tmp_path):
    """A reading's configuration must be recoverable from its own record. The
    claim carries a copy so the claims file reads alone; this is where the copy
    is taken from, and it cannot drift because both are one append."""
    log = CallLog(tmp_path)
    transport = answering()

    call, _ = ask(
        transport,
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION.model_copy(update={"temperature": 0.0}),
    )

    assert transport.calls[0]["temperature"] == 0.0
    assert call.temperature == 0.0
    assert log.all()[0].temperature == 0.0


def test_a_call_at_the_provider_s_own_default_records_no_temperature(tmp_path):
    """Absent rather than guessed. What a provider defaults to is its business
    and moves without notice, so a number written here would be a fact about
    the record rather than about the request."""
    log = CallLog(tmp_path)

    call, _ = ask(
        answering(),
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION,
    )

    assert call.temperature is None


def test_the_execution_and_its_last_request_are_both_recorded(tmp_path, monkeypatch):
    """Two levels: what the caller waited and how many requests that took,
    then the request that answered. Their difference is the endpoint's."""
    ticks = iter([100.0, 100.25])
    monkeypatch.setattr(ASK, "monotonic", lambda: next(ticks))
    log = CallLog(tmp_path)
    transport = answering()
    transport.reply = replace(transport.reply, request_ms=90, attempts=2)

    ask(
        transport,
        log,
        system="sys",
        content="body",
        configuration=CONFIGURATION,
    )

    (stored,) = log.all()
    assert (stored.elapsed_ms, stored.attempts, stored.request_ms) == (250, 2, 90)


def test_a_failure_records_both_levels_too(tmp_path, monkeypatch):
    """A request that failed instantly and one that timed out after five tries
    are different facts about an endpoint, and the failure is where knowing
    which matters."""
    ticks = iter([0.0, 30.0])
    monkeypatch.setattr(ASK, "monotonic", lambda: next(ticks))
    log = CallLog(tmp_path)
    failure = RuntimeError("timed out")
    stamp(failure, Trace(attempts=5, request_ms=9_000))

    with pytest.raises(RuntimeError):
        ask(
            FakeTransport(error=failure),
            log,
            system="sys",
            content="body",
            configuration=CONFIGURATION,
        )

    (stored,) = log.all()
    assert (stored.elapsed_ms, stored.attempts, stored.request_ms) == (30_000, 5, 9_000)


def test_a_transport_that_never_retried_stamps_nothing(tmp_path):
    """Absent rather than claimed: a count nothing kept is not a count of
    one."""
    log = CallLog(tmp_path)

    with pytest.raises(RuntimeError):
        ask(
            FakeTransport(error=RuntimeError("no key")),
            log,
            system="sys",
            content="body",
            configuration=CONFIGURATION,
        )

    (stored,) = log.all()
    assert (stored.attempts, stored.request_ms) == (None, None)


def test_a_call_from_before_the_waits_were_measured_still_reads():
    """Additive, like every other field: the log stays readable by its own
    schema, and an unmeasured call says so rather than claiming zero."""
    stored = Call.model_validate_json(
        recorded(
            model="m", effort="low", prompt="p", prompt_hash="h", response="r"
        ).model_dump_json(exclude={"elapsed_ms"})
    )

    assert stored.elapsed_ms is None
