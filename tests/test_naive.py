import json
from dataclasses import dataclass, field

import pytest
from matching import card, seeded
from pydantic import ValidationError

from algo_coach.calls import CallLog, Reply
from algo_coach.generation import GenerationError, naive
from algo_coach.generation.blind import SYSTEM as BLIND
from algo_coach.generation.blind import prompt as blindly
from algo_coach.generation.clock import (
    CLOCK_DEFAULT,
    SYSTEM,
    prompt,
    read,
    request_hash,
    schema,
)
from algo_coach.schema import Configuration

STATEMENT = "Given a list of readings, return the widest stretch that stays fair."
AVOID = "two indices walking one way over a window that never shrinks"


@dataclass
class FakeModel:
    text: str | None
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        return Reply(text=self.text, stop_reason="stop" if self.text else "length")


def answer(solution: str = "def solve(xs):\n    return len(xs)\n") -> str:
    return json.dumps({"solution": solution})


# a site aimed elsewhere: every field is named, since none has a default
ELSEWHERE = Configuration(model="another", effort="low", pin="somewhere")


def test_the_form_to_avoid_is_sent_beside_the_statement(tmp_path):
    """It settles no case and discards no problem, so naming the form cannot
    reach a verdict. No other site may be told it."""
    model = FakeModel(answer())

    code, call = naive(model, CallLog(tmp_path), STATEMENT, AVOID)

    assert model.calls[0]["content"] == prompt(STATEMENT, AVOID)
    assert STATEMENT in model.calls[0]["content"] and AVOID in model.calls[0]["content"]
    assert code.startswith("def solve")
    assert call.response == answer()


def test_the_brief_asks_for_the_replaced_approach_where_the_blind_one_asks_for_plain(
    tmp_path,
):
    """A plain solution is whatever the model finds obvious, which on some
    statements is the form itself. This one is told what is wanted: what a
    solver writes without the technique, rather than the slowest solution
    there is."""
    (one,) = seeded(tmp_path, card())
    sent = SYSTEM + prompt(STATEMENT, one.templates[0].trigger)

    assert "solver reaches for without one technique" in SYSTEM
    assert "slowest" not in SYSTEM
    assert one.templates[0].trigger in sent
    # the blind site is briefed for the plainest solution and shown no form,
    # which is what keeps its reading of the statement independent
    assert one.templates[0].trigger not in BLIND + blindly(STATEMENT)


def test_the_brief_bounds_the_candidates_by_the_statement(tmp_path):
    """A clock that only tries the values the input contains has used the
    insight the fast solution is built on, and separates nothing."""
    assert "The candidates are what the statement's own bounds admit" in SYSTEM
    assert "the values the input happens to contain" in SYSTEM


def test_the_brief_stops_a_clock_slower_than_the_replaced_approach():
    """Told to be slowest, a model enumerated every pairing. The search then
    separates at a few dozen elements, which is below the size a submission of
    the wrong complexity is judged at."""
    assert "Do not search a space wider than the definition names" in SYSTEM


def test_a_reply_carrying_no_solution_fails():
    with pytest.raises(ValidationError):
        read(json.dumps({"solution": ""}))


def test_an_answer_cut_short_writes_no_solution(tmp_path):
    model = FakeModel(None)

    with pytest.raises(GenerationError):
        naive(model, CallLog(tmp_path), STATEMENT, AVOID)

    assert len(CallLog(tmp_path).all()) == 1


def test_the_site_s_own_configuration_is_the_default(tmp_path):
    model = FakeModel(answer())

    naive(model, CallLog(tmp_path), STATEMENT, AVOID)
    naive(model, CallLog(tmp_path), STATEMENT, AVOID, configuration=ELSEWHERE)

    assert model.calls[0]["model"] == CLOCK_DEFAULT.model
    assert model.calls[1]["model"] == ELSEWHERE.model


def test_the_site_is_sampled_where_the_other_answering_ones_are_greedy(tmp_path):
    """It produces an artifact rather than a verdict, so a second call is a
    second draw where the first wrote the form.

    Left to the provider rather than set here, as generation's is: a model
    reasoning at an effort accepts no temperature, and its endpoint drops the
    request the moment one is sent.
    """
    model = FakeModel(answer())

    _, call = naive(model, CallLog(tmp_path), STATEMENT, AVOID)

    assert model.calls[0]["temperature"] is None
    assert call.temperature is None


def test_two_forms_to_avoid_are_two_questions(tmp_path):
    """The digest keys the skip, so a template whose trigger was edited is
    re-asked and the rest are not."""
    assert request_hash(STATEMENT, AVOID) != request_hash(STATEMENT, "something else")


def test_the_schema_is_strict():
    shape = schema()

    assert sorted(shape["required"]) == sorted(shape["properties"])
    assert shape["additionalProperties"] is False
