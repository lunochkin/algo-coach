import json
from dataclasses import dataclass, field

import pytest
from helpers import a_call
from pydantic import ValidationError

from algo_coach.calls import CallLog, Configuration, Reply
from algo_coach.generation import GenerationError
from algo_coach.generation.inputs import INPUTS_DEFAULT, SYSTEM, builder, prompt, read, schema
from algo_coach.generation.speedup import search
from algo_coach.runner import defines_solve, outputs
from algo_coach.schema import MachineProvenance

STATEMENT = "Given a list of at most 1000 readings, return the widest fair stretch."
BUILDS = "def solve(size, seed):\n    return [list(range(size))]\n"
SLEEPS = "import time\n\n\ndef solve(xs):\n    time.sleep(len(xs) / 100)\n    return len(xs)\n"


@dataclass
class FakeModel:
    text: str | None
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        return Reply(text=self.text, stop_reason="stop" if self.text else "length")


def answer(code: str = BUILDS, largest: int = 1000) -> str:
    return json.dumps({"code": code, "largest": largest})


# a site aimed elsewhere: every field is named, since none has a default
ELSEWHERE = Configuration(model="another", effort="low", pin="somewhere")


def test_the_statement_is_the_whole_of_the_request(tmp_path):
    """The constraints are what the generator reads, and the statement is
    where they are stated."""
    model = FakeModel(answer())

    built, call = builder(model, CallLog(tmp_path), STATEMENT)

    assert model.calls[0]["content"] == f"<problem>\n{STATEMENT}\n</problem>"
    assert built.code == BUILDS
    assert call.response == answer()


def test_the_largest_size_the_statement_allows_is_reported(tmp_path):
    """The search asks for sizes, and an input above the bound separates
    nothing because the problem excludes it."""
    model = FakeModel(answer(largest=1000))

    built, _ = builder(model, CallLog(tmp_path), STATEMENT)

    assert built.largest == 1000


def test_the_generator_defines_the_entry_point_every_module_defines():
    """Run through the same executor as a solution, so the fixed name is what
    it has to define."""
    assert defines_solve(BUILDS)


def test_what_it_builds_is_the_arguments_of_a_case():
    """The reply is code, and what makes it usable is that its return is the
    positional arguments a solution takes."""
    [built] = outputs(BUILDS, [[4, 0]], cap_ms=1000)

    assert built == [[0, 1, 2, 3]]


def test_the_search_runs_a_generated_builder():
    """What the call exists for: the search had no input to run without one."""
    found = search(
        lambda size: outputs(BUILDS, [[size, 0]], cap_ms=1000)[0],
        canonical="def solve(xs):\n    return len(xs)\n",
        naive=SLEEPS,
        reference="def solve(xs):\n    return len(xs)\n",
        written=MachineProvenance.of(a_call()),
        cap_ms=55,
        largest=16,
        measure_ms=2000,
    )

    assert found.found
    # what the call's own code built at the size the clock decided, rather than
    # a size a loaded machine moves by one
    assert found.args == [list(range(found.size))]


def test_a_bound_of_nothing_is_rejected():
    """A largest size of zero admits no input at all."""
    with pytest.raises(ValidationError):
        read(answer(largest=0))


def test_a_reply_carrying_no_code_fails():
    with pytest.raises(ValidationError):
        read(answer(code=""))


def test_an_answer_cut_short_writes_no_generator(tmp_path):
    model = FakeModel(None)

    with pytest.raises(GenerationError):
        builder(model, CallLog(tmp_path), STATEMENT)

    assert len(CallLog(tmp_path).all()) == 1


def test_the_brief_asks_for_one_input_per_pair(tmp_path):
    """Two runs at one size and seed would build two cases, and the stored one
    could not be reproduced from the two numbers."""
    assert "same pair builds the same input" in SYSTEM


def test_the_brief_names_no_technique_and_no_form():
    """The generator reads the constraints, which are what a statement states
    rather than what it withholds."""
    sent = SYSTEM + prompt(STATEMENT)

    for named in ("Technique:", "Cue:", "Form:"):
        assert named not in sent


def test_the_schema_is_strict():
    shape = schema()

    assert sorted(shape["required"]) == sorted(shape["properties"])
    assert shape["additionalProperties"] is False


def test_the_site_s_own_configuration_is_the_default(tmp_path):
    """A site names its own model, and a run may aim this call elsewhere."""
    model = FakeModel(answer())

    builder(model, CallLog(tmp_path), STATEMENT)
    builder(model, CallLog(tmp_path), STATEMENT, configuration=ELSEWHERE)

    assert model.calls[0]["model"] == INPUTS_DEFAULT.model
    assert model.calls[1]["model"] == ELSEWHERE.model
