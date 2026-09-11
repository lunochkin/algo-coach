import json
from dataclasses import dataclass, field

import pytest
from helpers import own
from matching import card, seeded, template
from pydantic import ValidationError

from algo_coach.calls import CallLog, Reply
from algo_coach.generation import GenerationError, Target, write_naive
from algo_coach.generation.blind import SYSTEM as BLIND
from algo_coach.generation.blind import prompt as blindly
from algo_coach.generation.naive import (
    NAIVE_DEFAULT,
    SYSTEM,
    prompt,
    read,
    request_hash,
    schema,
)
from algo_coach.schema import Configuration

STATEMENT = "Given a list of readings, return the widest stretch that stays fair."
AVOIDING = "two indices walking one way over a window that never shrinks"


def aimed(root, trigger: str = AVOIDING) -> Target:
    """The card and the form a writing was aimed at, which is what the naive
    site's prompt is built from."""
    (one,) = seeded(root, card(templates=[template("longest-valid-window", trigger=trigger)]))
    return Target(card=one, template=one.templates[0])


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


def test_the_form_to_avoid_is_sent_beside_the_statement(database):
    """It settles no case and rejects no draft, so naming the form cannot
    reach a verdict. No other site may be told it."""
    model = FakeModel(answer())

    target = aimed(database)

    code, call = write_naive(model, CallLog(database), STATEMENT, target)

    assert model.calls[0]["content"] == prompt(STATEMENT, target)
    assert STATEMENT in model.calls[0]["content"] and AVOIDING in model.calls[0]["content"]
    assert code.startswith("def solve")
    assert call.response == answer()


def test_the_brief_asks_for_the_replaced_approach_where_the_blind_one_asks_for_plain(
    database,
):
    """A plain solution is whatever the model finds obvious, which on some
    statements is the form itself. This one is told what is wanted: what a
    solver writes without the technique, rather than the slowest solution
    there is."""
    target = aimed(database)
    sent = SYSTEM + prompt(STATEMENT, target)

    assert "solver reaches for without one technique" in SYSTEM
    assert "slowest" not in SYSTEM
    assert target.template.trigger in sent
    # the blind site is prompted for the plainest solution and shown no form,
    # which is what keeps its reading of the statement independent
    assert target.template.trigger not in BLIND + blindly(STATEMENT)


def test_the_brief_bounds_the_candidates_by_the_statement(tmp_path):
    """A naive solution that only tries the values the input contains has used
    the insight the fast solution is built on, and separates nothing."""
    assert "The candidates are what the statement's own bounds admit" in SYSTEM
    assert "the values the input happens to contain" in SYSTEM


def test_the_brief_stops_a_naive_solution_slower_than_the_replaced_approach():
    """Told to be slowest, a model enumerated every pairing. The search then
    separates at a few dozen elements, which is below the size a submission of
    the wrong complexity is judged at."""
    assert "Do not search a space wider than the definition names" in SYSTEM


def test_a_reply_carrying_no_solution_fails():
    with pytest.raises(ValidationError):
        read(json.dumps({"solution": ""}))


def test_an_answer_cut_short_writes_no_solution(database):
    model = FakeModel(None)

    with pytest.raises(GenerationError):
        write_naive(model, CallLog(database), STATEMENT, aimed(database))

    assert len(own(CallLog(database).all())) == 1


def test_the_site_s_own_configuration_is_the_default(database):
    model = FakeModel(answer())

    target = aimed(database)
    write_naive(model, CallLog(database), STATEMENT, target)
    write_naive(model, CallLog(database), STATEMENT, target, configuration=ELSEWHERE)

    assert model.calls[0]["model"] == NAIVE_DEFAULT.model
    assert model.calls[1]["model"] == ELSEWHERE.model


def test_the_site_is_sampled_where_the_other_answering_ones_are_greedy(database):
    """It produces an artifact rather than a verdict, so a second call is a
    second draw where the first wrote the form.

    Left to the provider rather than set here, as generation's is: a model
    reasoning at an effort accepts no temperature, and its endpoint drops the
    request the moment one is sent.
    """
    model = FakeModel(answer())

    _, call = write_naive(model, CallLog(database), STATEMENT, aimed(database))

    assert model.calls[0]["temperature"] is None
    assert call.temperature is None


def test_two_forms_to_avoid_are_two_questions(database):
    """The prompt hash keys the skip, so a template whose trigger was edited is
    re-asked and the rest are not."""
    assert request_hash(STATEMENT, aimed(database)) != request_hash(
        STATEMENT, aimed(database, trigger="something else")
    )


def test_the_technique_that_earns_the_form_is_sent_beside_it(database):
    """A card lists the forms it teaches, and a model reaches the technique
    through one it does not: tabulation where the form is a memo."""
    sent = prompt(STATEMENT, aimed(database))

    assert "sliding-window" in sent
    assert "Earns it:" in sent


def test_the_schema_is_strict():
    shape = schema()

    assert sorted(shape["required"]) == sorted(shape["properties"])
    assert shape["additionalProperties"] is False
