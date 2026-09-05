import json
from dataclasses import dataclass, field

import pytest
from matching import card, seeded
from pydantic import ValidationError

from algo_coach.calls import CallLog, Reply
from algo_coach.generation import GenerationError, reference
from algo_coach.generation.blind import BLIND_DEFAULT, SYSTEM, prompt, read, schema
from algo_coach.generation.generator import prompt as brief
from algo_coach.schema import Configuration

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


# a site aimed elsewhere: every field is named, since none has a default
ELSEWHERE = Configuration(model="another", effort="low", pin="somewhere")


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


def test_the_site_s_own_configuration_is_the_default(tmp_path):
    """A site names its own model. Independence is what this call was shown,
    so it may run the model that wrote the statement."""
    model = FakeModel(answer())

    reference(model, CallLog(tmp_path), STATEMENT)
    reference(model, CallLog(tmp_path), STATEMENT, configuration=ELSEWHERE)

    assert model.calls[0]["model"] == BLIND_DEFAULT.model
    assert model.calls[1]["model"] == ELSEWHERE.model


def test_the_schema_is_strict():
    shape = schema()

    assert sorted(shape["required"]) == sorted(shape["properties"])
    assert shape["additionalProperties"] is False
