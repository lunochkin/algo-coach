import json
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from algo_coach.calls import UNSENT, CallLog, Reply
from algo_coach.classifier import (
    DEFAULT,
    EFFORT,
    MODEL,
    PIN,
    SYSTEM,
    ClassifierError,
    request_hash,
)
from algo_coach.classifier import classify as _classify
from algo_coach.schema import Kind
from algo_coach.techniques import criteria

CODE = "def f(nums):\n    return sorted(nums)\n"

# One throwaway call log for the whole module: these tests are about the
# request, and where the record of it lands is another module's subject.
CALLS = CallLog(Path(tempfile.mkdtemp()))


def verdict(client, candidates, code, **kwargs):
    """`classify` without its call, which only the write path needs."""
    techniques, _ = _classify(client, CALLS, candidates, code, **kwargs)
    return techniques


@dataclass
class FakeTransport:
    """Records the request rather than making one — the prompt is the thing
    under test, and a real call would score a live model, not this code."""

    techniques: list[str]
    silent: bool = False
    # The token cap, where whatever came back is truncated. `text` carries the
    # runaway that emits whitespace until it runs out; without it, the reply
    # that never reached the schema at all.
    stop_reason: str = "stop"
    text: str | None = None
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        if self.silent:
            # A refusal answers nothing and says nothing about the code.
            return Reply(text=None, stop_reason="content_filter")
        if self.stop_reason != "stop":
            return Reply(text=self.text, stop_reason=self.stop_reason)
        return Reply(text=json.dumps({"techniques": self.techniques}), stop_reason="stop")


def answering(*techniques: str) -> FakeTransport:
    return FakeTransport(list(techniques))


def test_the_verdict_is_the_techniques_it_named():
    client = answering("greedy")

    assert verdict(client, ["greedy", "sorting"], CODE) == ["greedy"]


def test_several_techniques_can_be_named():
    """A solution can combine them, so the answer is a set, not a choice."""
    client = answering("sorting", "greedy")

    assert verdict(client, ["greedy", "sorting"], CODE) == ["greedy", "sorting"]


def test_the_candidates_are_the_only_answers_the_schema_allows():
    """It narrows what a problem could exercise; it never invents a technique
    the tags do not name."""
    client = answering("greedy")

    verdict(client, ["greedy", "sorting"], CODE)

    schema = client.calls[0]["schema"]
    assert schema["properties"]["techniques"]["items"]["enum"] == ["greedy", "sorting"]


def test_the_candidates_are_named_in_the_prompt_too():
    """The schema enforces them only at emission. Thinking is not constrained,
    so a model meeting them there would read the code without knowing which
    answers exist."""
    client = answering("greedy")

    verdict(client, ["greedy", "sorting"], CODE)

    (call,) = client.calls
    assert "greedy, sorting" in call["content"]


def test_each_candidate_reaches_the_model_with_its_criterion():
    """One rulebook, applied where it decides something: the reading is made
    against what earns a code and the near miss it is confused with."""
    client = answering("greedy")

    verdict(client, ["greedy", "sorting"], CODE)

    (call,) = client.calls
    content = call["content"]
    for candidate in ("greedy", "sorting"):
        entry = criteria()[candidate]
        assert entry.earns in content
        assert entry.near_miss in content
        assert str(entry.kind) in content


def test_a_candidate_carries_its_kind_as_a_test_not_a_label():
    """One question is answered four ways, and a bare kind name only helps a
    reader who already knows which way — which is how a structure comes to be
    judged on whether it was performed."""
    client = answering("greedy")

    verdict(client, ["greedy", "binary-search-tree"], CODE)

    (call,) = client.calls
    content = call["content"]
    assert Kind.PARADIGM.test in content
    assert Kind.STRUCTURE.test in content


def test_a_criterion_is_paid_for_only_where_its_code_is_a_candidate():
    """Which is why it is rendered here and not in the system text — every
    call would carry all 27, and a call decides between two or three."""
    client = answering("greedy")

    verdict(client, ["greedy", "sorting"], CODE)

    (call,) = client.calls
    assert criteria()["trie"].earns not in call["content"]


def test_the_system_text_carries_no_per_code_rule():
    """A rule about one code in the text every call pays for is a criterion in
    the wrong file: it belongs to the vocabulary entry, which travels with the
    candidate."""
    for code in criteria():
        assert not re.search(rf"\b{re.escape(code)}\b", SYSTEM)


def test_a_retired_candidate_carries_no_criterion_and_still_asks():
    """Records outlive the vocabulary, so a stored problem can name a code the
    criteria no longer hold. A missing rule costs its own line, not the
    call."""
    client = answering("greedy")

    verdict(client, ["greedy", "dynamic-programming-2d"], CODE)

    (call,) = client.calls
    assert "greedy, dynamic-programming-2d" in call["content"]


def test_a_technique_outside_the_candidates_is_dropped():
    """The schema's guarantee ends with the request and the record does not —
    an unknown code must never reach an append-only log."""
    client = answering("greedy", "dynamic-programming")

    assert verdict(client, ["greedy", "sorting"], CODE) == ["greedy"]


def test_the_verdict_is_ordered_by_the_candidates():
    """Scored by set equality, so order carries nothing — fixing it keeps two
    runs on the same problem comparable."""
    client = answering("sorting", "greedy")

    assert verdict(client, ["greedy", "sorting"], CODE) == ["greedy", "sorting"]


def test_naming_nothing_is_a_legal_verdict():
    """The tags may not cover what the code did. An empty verdict writes no
    claim and leaves the fallback standing, rather than asserting a wrong
    one."""
    client = answering()

    assert verdict(client, ["greedy", "sorting"], CODE) == []


def test_the_code_is_what_it_reads():
    client = answering("greedy")

    verdict(client, ["greedy", "sorting"], CODE)

    (call,) = client.calls
    assert CODE in call["content"]


def test_one_candidate_decides_nothing_and_costs_no_call():
    """The fallback already answers it, and the schema would offer one
    choice."""
    client = answering("greedy")

    assert verdict(client, ["greedy"], CODE) == ["greedy"]
    assert client.calls == []


def test_no_candidates_is_no_question():
    client = answering()

    assert verdict(client, [], CODE) == []
    assert client.calls == []


def test_a_response_carrying_no_verdict_raises():
    """A refusal and a truncated answer both land here: the caller is running
    over a backlog, and one attempt must not cost the rest."""
    client = FakeTransport([], silent=True)

    with pytest.raises(ClassifierError, match="content_filter"):
        verdict(client, ["greedy", "sorting"], CODE)


def test_an_unsent_effort_is_left_off_the_call():
    """Some models reject the parameter outright, so a level that means "the
    model's own" travels as itself and the transport leaves it off the wire."""
    client = answering("greedy")

    verdict(
        client,
        ["greedy", "sorting"],
        CODE,
        configuration=DEFAULT.model_copy(update={"model": "a-model", "effort": UNSENT}),
    )

    (call,) = client.calls
    assert call["effort"] == UNSENT
    # The schema is unaffected: what the model is asked to think with and what
    # it is allowed to answer are separate requests of it.
    assert call["schema"]["properties"]["techniques"]["items"]["enum"] == ["greedy", "sorting"]


def test_the_pin_travels_with_the_model_it_belongs_to():
    """A configuration says which build served it, since an endpoint carries
    some models and not others — one setting for a whole run would be wrong
    the moment two models are compared."""
    client = answering("greedy")

    verdict(
        client,
        ["greedy", "sorting"],
        CODE,
        configuration=DEFAULT.model_copy(
            update={"model": "a-model", "effort": "low", "pin": "a-host"}
        ),
    )

    (call,) = client.calls
    assert call["pin"] == "a-host"


def test_the_built_in_configuration_is_what_a_caller_naming_none_gets():
    client = answering("greedy")

    verdict(client, ["greedy", "sorting"], CODE)

    (call,) = client.calls
    assert (call["model"], call["effort"]) == (MODEL, EFFORT)


def test_a_named_configuration_is_what_the_call_carries():
    """What makes a second classifier readable at all: the flag has to reach
    the request, not only the record written from it."""
    client = answering("greedy")

    verdict(
        client,
        ["greedy", "sorting"],
        CODE,
        configuration=DEFAULT.model_copy(update={"model": "a-cheap-model", "effort": "low"}),
    )

    (call,) = client.calls
    assert (call["model"], call["effort"]) == ("a-cheap-model", "low")


def test_the_default_configuration_is_known_in_every_part():
    """A machine claim can be recomputed by a better classifier, so re-deriving
    has to find the stale ones and leave the rest — and a reading whose
    configuration is partly unknown compares with nothing.

    Which model is named is a decision the eval set makes and remakes; that it
    is named, pinned and sampled deliberately is the rule. A literal id here
    would assert only that someone typed one.
    """
    assert (DEFAULT.model, DEFAULT.effort, DEFAULT.pin) == (MODEL, EFFORT, PIN)
    assert all((MODEL, EFFORT, PIN))
    # Greedy rather than absent: the sweep writes permanently, so a sampled
    # default would make the same fraction of a percent permanent with it.
    assert DEFAULT.temperature == 0.0


def test_the_request_hash_is_the_question_this_attempt_would_be_asked():
    """What decides whether a reading is worth paying for again — recomputed
    rather than compared with a literal, which would assert only that someone
    edited it."""
    assert request_hash(["greedy", "sorting"], CODE) == request_hash(["greedy", "sorting"], CODE)


def test_a_different_solution_is_a_different_question():
    assert request_hash(["greedy", "sorting"], CODE) != request_hash(["greedy", "sorting"], "pass")


def test_a_different_candidate_is_a_different_question():
    """Because a criterion travels with its candidate: editing one entry
    changes this for the attempts carrying that code and for no others."""
    assert request_hash(["greedy", "sorting"], CODE) != request_hash(["greedy", "trie"], CODE)


def test_the_request_hash_is_short_enough_to_store_on_every_claim():
    """Only ever compared for equality, so the collision margin is irrelevant;
    sixty-four characters on every line of an append-only log is not."""
    assert len(request_hash(["greedy", "sorting"], CODE)) == 12


def test_a_reply_cut_short_by_the_cap_names_nothing():
    """The decoder ran out of tokens, so whatever came back is truncated and
    no verdict can be read from it. Recorded as naming nothing rather than
    raised. Greedy decoding is deterministic, so every later run would re-ask
    the same prompt and be cut short in the same place."""
    client = FakeTransport([], stop_reason="length", text="{  \t  \n\n  \t  ")

    techniques, call = _classify(client, CALLS, ["greedy", "sorting"], CODE)

    assert techniques == []
    assert call is not None and call.stop_reason == "length"


def test_a_cap_hit_that_returned_no_text_names_nothing_too():
    """Both shapes of the same event. Which one arrives depends on whether the
    runaway was inside the schema or before it, and neither can be read."""
    client = FakeTransport([], stop_reason="length")

    techniques, call = _classify(client, CALLS, ["greedy", "sorting"], CODE)

    assert techniques == []


def test_a_refusal_still_raises():
    """It answered nothing and says nothing about the code. Only the cap is
    stored as a verdict, because only the cap repeats."""
    with pytest.raises(ClassifierError):
        _classify(FakeTransport([], silent=True), CALLS, ["greedy", "sorting"], CODE)
