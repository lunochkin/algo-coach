import json
from dataclasses import dataclass, field

import pytest

from algo_coach.calls import CallLog, Configuration, Reply
from algo_coach.generation import GenerationError, separators
from algo_coach.generation.discrimination import DISCRIMINATION_DEFAULT, prompt, read, schema
from algo_coach.mutation import Mutant, Operator

STATEMENT = "Given a list of readings, return the widest stretch that stays fair."
CANONICAL = "def solve(xs):\n    return len(xs)\n"
SURVIVOR = Mutant(
    code="def solve(xs):\n    return len(xs) + 1\n",
    operator=Operator.CONSTANT,
    change="1 → 2",
    line=2,
)


@dataclass
class FakeModel:
    text: str | None
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        return Reply(text=self.text, stop_reason="stop" if self.text else "length")


def answer(*args) -> str:
    return json.dumps({"cases": [{"args": json.dumps(list(one))} for one in args]})


def asked(model: FakeModel, **overrides):
    return separators(
        model, CallLog(overrides.pop("tmp_path")), STATEMENT, canonical=CANONICAL, **overrides
    )


# a site aimed elsewhere: every field is named, since none has a default
ELSEWHERE = Configuration(model="another", effort="low", pin="somewhere")


def test_the_reply_carries_arguments_alone(tmp_path):
    """A model that wrote the expected value could write the mutant's own
    answer, and the case would then fail the correct solution."""
    model = FakeModel(answer([[1, 2]], [3]))

    proposed, call = asked(model, survivors=[SURVIVOR], tmp_path=tmp_path)

    assert proposed == [[[1, 2]], [3]]
    assert call.response == answer([[1, 2]], [3])


def test_the_request_carries_the_statement_the_solution_and_the_mutant(tmp_path):
    """The three the reply is derived from: what the problem asks, what is
    correct, and the change nothing caught."""
    model = FakeModel(answer([[1]]))

    asked(model, survivors=[SURVIVOR], tmp_path=tmp_path)

    sent = model.calls[0]["content"]
    assert f"<problem>\n{STATEMENT}\n</problem>" in sent
    assert CANONICAL in sent
    assert SURVIVOR.code in sent


def test_the_mutant_is_shown_with_the_change_it_carries(tmp_path):
    """One decision is named, where a diff of two whole solutions has to be
    found first."""
    model = FakeModel(answer([[1]]))

    asked(model, survivors=[SURVIVOR], tmp_path=tmp_path)

    assert "change='1 → 2' line=2" in model.calls[0]["content"]


def test_every_survivor_reaches_one_call(tmp_path):
    """One call rather than one per mutant: a proposal that separates nothing
    costs the case it would have added, not the batch."""
    other = Mutant(
        code="def solve(xs):\n    return 0\n", operator=Operator.CONSTANT, change="1 → 0", line=2
    )
    model = FakeModel(answer([[1]]))

    asked(model, survivors=[SURVIVOR, other], tmp_path=tmp_path)

    assert len(model.calls) == 1
    assert other.code in model.calls[0]["content"]


def test_the_cases_the_set_already_holds_are_named(tmp_path):
    """Unshown, the reply proposes what the set already has, and the survivor
    is still standing."""
    model = FakeModel(answer([[1]]))

    asked(model, survivors=[SURVIVOR], known=[[[1, 2, 3]]], tmp_path=tmp_path)

    assert "[[1, 2, 3]]" in model.calls[0]["content"]


def test_an_empty_set_of_known_cases_names_no_heading(tmp_path):
    """A heading with nothing under it reads as a field left blank."""
    model = FakeModel(answer([[1]]))

    asked(model, survivors=[SURVIVOR], tmp_path=tmp_path)

    assert "already has" not in model.calls[0]["content"]


def test_no_call_is_paid_for_where_nothing_survived(tmp_path):
    """The set caught every change, so there is no question to ask."""
    model = FakeModel(answer([[1]]))

    with pytest.raises(ValueError):
        asked(model, survivors=[], tmp_path=tmp_path)

    assert model.calls == []


def test_an_answer_cut_short_proposes_nothing(tmp_path):
    model = FakeModel(None)

    with pytest.raises(GenerationError):
        asked(model, survivors=[SURVIVOR], tmp_path=tmp_path)

    assert len(CallLog(tmp_path).all()) == 1


def test_a_reply_proposing_no_case_is_read_as_a_verdict():
    """A survivor equivalent to the canonical is separated by no input, so an
    empty reply is that answer. Rejected, it would fail the round's call and
    hold a draft every resume asks the same question of."""
    assert read(json.dumps({"cases": []})) == []


def test_the_reply_has_no_field_for_an_expected_value():
    """The record shape is what stops a model writing one, rather than the
    prose asking it not to."""
    assert "expected" not in json.dumps(schema())


def test_the_schema_is_strict():
    shape = schema()

    assert sorted(shape["required"]) == sorted(shape["properties"])
    assert shape["additionalProperties"] is False
    assert shape["properties"]["cases"]["items"]["additionalProperties"] is False


def test_the_site_s_own_configuration_is_the_default(tmp_path):
    """A site names its own model, and a run may aim this call elsewhere."""
    model = FakeModel(answer([[1]]))

    asked(model, survivors=[SURVIVOR], tmp_path=tmp_path)
    asked(model, survivors=[SURVIVOR], configuration=ELSEWHERE, tmp_path=tmp_path)

    assert model.calls[0]["model"] == DISCRIMINATION_DEFAULT.model
    assert model.calls[1]["model"] == ELSEWHERE.model


def test_a_known_case_is_shown_as_arguments_alone():
    """The set's expected values are withheld. The solution above says how the
    problem behaves, and a list of answers is what a reply could copy from."""
    sent = prompt(STATEMENT, CANONICAL, [SURVIVOR], known=[[[1, 2, 3]]])

    assert "[[1, 2, 3]]" in sent
    assert "expected" not in sent
