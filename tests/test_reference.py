"""The reference call: the statement in, a solution out, and nothing that
would let it inherit the canonical's reading."""

import json
from dataclasses import dataclass, field

import pytest
from matching import card, seeded
from pydantic import ValidationError

from algo_coach.calls import CallLog, Reply
from algo_coach.generation import Configuration, GenerationError, reference
from algo_coach.generation.blind import SYSTEM, prompt, read, schema
from algo_coach.generation.generator import prompt as brief

STATEMENT = "Given a list of readings, return the widest stretch that stays fair."


@dataclass
class FakeModel:
    text: str | None
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        return Reply(text=self.text, stop_reason="stop" if self.text else "length")


def answer(solution: str = "def solve(xs):\n    return len(xs)\n") -> str:
    return json.dumps({"solution": solution})


def test_the_statement_is_the_whole_of_the_request(tmp_path):
    """Shown the canonical or its cases, the reference inherits that
    solution's reading, and agreement then shows only self-consistency."""
    model = FakeModel(answer())

    code, call = reference(model, CallLog(tmp_path), STATEMENT)

    assert model.calls[0]["content"] == f"<problem>\n{STATEMENT}\n</problem>"
    assert code.startswith("def solve")
    assert call.response == answer()


def test_the_brief_names_no_technique_and_no_form(tmp_path):
    """The template, its cue and the form are what the statement is written to
    withhold, so none of them may reach the reference."""
    (one,) = seeded(tmp_path, card())
    sent = SYSTEM + prompt(STATEMENT)

    for named in ("Technique:", "Cue:", "Form:", one.templates[0].code):
        assert named not in sent
    # The generation brief carries every one of them, which is what makes the
    # two readings independent rather than one reading twice.
    assert one.templates[0].code in brief(one, one.templates[0])


def test_a_reply_carrying_no_solution_fails():
    with pytest.raises(ValidationError):
        read(json.dumps({"solution": ""}))


def test_an_answer_cut_short_writes_no_solution(tmp_path):
    model = FakeModel(None)

    with pytest.raises(GenerationError):
        reference(model, CallLog(tmp_path), STATEMENT)

    assert len(CallLog(tmp_path).all()) == 1


def test_the_configuration_is_the_generator_s_unless_named(tmp_path):
    """Independence is what the model was shown, not which model it was."""
    model = FakeModel(answer())

    reference(model, CallLog(tmp_path), STATEMENT)
    reference(model, CallLog(tmp_path), STATEMENT, configuration=Configuration(model="another"))

    assert model.calls[0]["model"] == Configuration().model
    assert model.calls[1]["model"] == "another"


def test_the_schema_is_strict():
    shape = schema()

    assert sorted(shape["required"]) == sorted(shape["properties"])
    assert shape["additionalProperties"] is False
