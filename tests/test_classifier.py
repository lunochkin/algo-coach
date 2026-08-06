import json
from dataclasses import dataclass, field
from hashlib import sha256

import pytest

from algo_coach.claims import EFFORT, MODEL, PROMPT_HASH, PROMPT_VERSION, ClassifierError, classify
from algo_coach.claims.classifier import SYSTEM

CODE = "def f(nums):\n    return sorted(nums)\n"


@dataclass
class Block:
    text: str
    type: str = "text"


@dataclass
class Response:
    content: list[Block]
    stop_reason: str = "end_turn"


@dataclass
class FakeMessages:
    """Records the request rather than making one — the prompt is the thing
    under test, and a real call would score a live model, not this code."""

    reply: Response | None = None
    calls: list[dict] = field(default_factory=list)

    def create(self, **kwargs) -> Response:
        self.calls.append(kwargs)
        return self.reply


@dataclass
class FakeClient:
    messages: FakeMessages


def answering(*techniques: str) -> FakeClient:
    text = json.dumps({"techniques": list(techniques)})
    return FakeClient(FakeMessages(Response([Block(text)])))


def test_the_verdict_is_the_techniques_it_named():
    client = answering("greedy")

    assert classify(client, ["greedy", "sorting"], CODE) == ["greedy"]


def test_several_techniques_can_be_named():
    """A solution can combine them, so the answer is a set, not a choice."""
    client = answering("sorting", "greedy")

    assert classify(client, ["greedy", "sorting"], CODE) == ["greedy", "sorting"]


def test_the_candidates_are_the_only_answers_the_schema_allows():
    """It narrows what a problem could exercise; it never invents a technique
    the tags do not name."""
    client = answering("greedy")

    classify(client, ["greedy", "sorting"], CODE)

    schema = client.messages.calls[0]["output_config"]["format"]["schema"]
    assert schema["properties"]["techniques"]["items"]["enum"] == ["greedy", "sorting"]


def test_the_candidates_are_named_in_the_prompt_too():
    """The schema enforces them only at emission. Thinking is not constrained,
    so a model meeting them there would read the code without knowing which
    answers exist."""
    client = answering("greedy")

    classify(client, ["greedy", "sorting"], CODE)

    (call,) = client.messages.calls
    assert "greedy, sorting" in call["messages"][0]["content"]


def test_a_technique_outside_the_candidates_is_dropped():
    """The schema's guarantee ends with the request and the record does not —
    an unknown code must never reach an append-only log."""
    client = answering("greedy", "dynamic-programming")

    assert classify(client, ["greedy", "sorting"], CODE) == ["greedy"]


def test_the_verdict_is_ordered_by_the_candidates():
    """Scored by set equality, so order carries nothing — fixing it keeps two
    runs on the same problem comparable."""
    client = answering("sorting", "greedy")

    assert classify(client, ["greedy", "sorting"], CODE) == ["greedy", "sorting"]


def test_naming_nothing_is_a_legal_verdict():
    """The tags may not cover what the code did. An empty verdict writes no
    claim and leaves the fallback standing, rather than asserting a wrong one."""
    client = answering()

    assert classify(client, ["greedy", "sorting"], CODE) == []


def test_the_code_is_what_it_reads():
    client = answering("greedy")

    classify(client, ["greedy", "sorting"], CODE)

    (call,) = client.messages.calls
    assert CODE in call["messages"][0]["content"]


def test_one_candidate_decides_nothing_and_costs_no_call():
    """The fallback already answers it, and the schema would offer one choice."""
    client = answering("greedy")

    assert classify(client, ["greedy"], CODE) == ["greedy"]
    assert client.messages.calls == []


def test_no_candidates_is_no_question():
    client = answering()

    assert classify(client, [], CODE) == []
    assert client.messages.calls == []


def test_a_response_carrying_no_verdict_raises():
    """A refusal and a truncated answer both land here: the caller is running
    over a backlog, and one attempt must not cost the rest."""
    client = FakeClient(FakeMessages(Response([], stop_reason="refusal")))

    with pytest.raises(ClassifierError, match="refusal"):
        classify(client, ["greedy", "sorting"], CODE)


def test_the_claim_records_what_produced_it():
    """Both count the same toward progress, but a machine claim can be
    recomputed by a better classifier, so re-deriving has to find the stale
    ones and leave the rest."""
    assert MODEL == "claude-opus-5"
    assert EFFORT
    assert PROMPT_VERSION
    assert PROMPT_HASH


def test_the_prompt_hash_is_the_text_that_was_sent():
    """Recomputed rather than compared with a literal: a hard-coded digest
    would need editing on every prompt edit and would assert only that someone
    edited it."""
    assert sha256(SYSTEM.encode()).hexdigest()[: len(PROMPT_HASH)] == PROMPT_HASH


def test_the_prompt_hash_changes_with_the_prompt():
    """What makes a forgotten version bump visible: two hashes under one
    version say the text moved and the version did not."""
    reflowed = SYSTEM.replace("\n\n", "\n")

    assert sha256(reflowed.encode()).hexdigest()[: len(PROMPT_HASH)] != PROMPT_HASH


def test_the_prompt_hash_is_short_enough_to_store_on_every_claim():
    """Only ever compared for equality, so the collision margin is irrelevant;
    sixty-four characters on every line of an append-only log is not."""
    assert len(PROMPT_HASH) == 12
