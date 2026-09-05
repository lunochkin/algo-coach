import json
from dataclasses import dataclass, field

import pytest
from helpers import PROVENANCE
from matching import card, seeded, template
from pydantic import ValidationError

from algo_coach.calls import CallLog, Reply, prompt_hash
from algo_coach.generation import (
    SYSTEM,
    GenerationError,
    generate,
    parameters,
    prompt,
    read,
    schema,
    written_for,
)
from algo_coach.schema import (
    Configuration,
    Problem,
    ProblemDifficulty,
    ProblemStatus,
    RetirementReason,
)


def brief(tmp_path, **overrides) -> str:
    (one,) = seeded(tmp_path, card(**overrides))
    return prompt(one, one.templates[0])


def test_the_form_is_sent_rather_than_named(tmp_path):
    """A cue and a title name a shape the model would have to guess at, so the
    code it comes back as is what the brief carries."""
    content = brief(tmp_path)

    assert "def longest_valid_window(): pass" in content
    assert "Cue: the cue for longest-valid-window" in content


def test_both_cues_reach_the_brief(tmp_path):
    """The technique's cue says when to reach for it at all, the template's
    which of its forms is being asked for."""
    content = brief(tmp_path)

    assert "Technique: sliding-window" in content
    assert "Reach for it when: a window over a contiguous run" in content


def test_notes_are_carried_where_the_template_has_them(tmp_path):
    content = brief(
        tmp_path,
        templates=[template("longest-valid-window", notes="Grow right.\nShrink left.")],
    )

    assert "Notes:\n  Grow right.\n  Shrink left." in content


def test_a_template_without_notes_carries_no_heading(tmp_path):
    """An empty heading reads as a field the author left blank."""
    assert "Notes:" not in brief(tmp_path)


def test_the_statement_is_asked_for_before_the_solution():
    """Cases read off a finished solution describe what that code does. The
    order in the brief is what makes them describe the problem instead."""
    parts = SYSTEM.index("1. A statement"), SYSTEM.index("2. A canonical"), SYSTEM.index("3. Test")

    assert list(parts) == sorted(parts)


def test_the_entry_point_convention_is_stated():
    """Nothing stores the name, so the brief is where a solution learns it."""
    assert "`solve`" in SYSTEM


def test_the_cue_s_own_settings_are_off_limits():
    """The monotonic-stack cue says "temperatures", and the probe returned the
    problem that cue was written from."""
    rule = " ".join(SYSTEM.split())

    assert "Your statement uses none of them." in rule
    assert "Choose a setting neither the cue nor the notes mentions." in rule


def draft(**overrides) -> str:
    return json.dumps(
        {
            "title": "Widest fair stretch",
            "statement": "Given a list of readings, return ...\n\ndef solve(xs)",
            "canonical": "def solve(xs):\n    return len(xs)\n",
            "difficulty": "medium",
            "cases": [{"args": "[[1, 2, 3]]", "expected": "3"}],
        }
        | overrides
    )


def test_the_three_parts_come_back_together():
    """One schema over all of them, so a reply carrying two fails rather than
    landing a problem with a part to fill in later."""
    written = read(draft())

    assert written.title == "Widest fair stretch"
    assert written.cases[0].args == [[1, 2, 3]]
    assert written.cases[0].expected == 3


def test_a_statement_carrying_no_signature_fails():
    """Three briefs are written from the statement alone, and a parameter
    order they infer is one they can infer differently."""
    with pytest.raises(ValidationError):
        read(draft(statement="Given a list of readings, return ..."))


def test_a_signature_the_canonical_contradicts_fails():
    """Both later solutions are written to the statement, so a line that
    disagrees with the canonical misleads them together."""
    with pytest.raises(ValidationError):
        read(draft(statement="Return ...\n\ndef solve(k, xs)"))


def test_the_declaration_is_read_and_not_a_mention_before_it():
    """A statement names the call while describing it, and the line it ends on
    is what a reader takes the order from."""
    written = read(
        draft(statement="`def solve(k, xs)` is described first.\n\ndef solve(xs) -> int:")
    )

    assert written.statement.endswith("def solve(xs) -> int:")


def test_an_annotated_signature_is_read_by_its_names():
    """A statement writing types and a canonical writing none are one
    order."""
    written = read(draft(statement="Return ...\n\ndef solve(xs: list[int]) -> int:"))

    assert parameters(written.canonical) == parameters(written.statement)


@pytest.mark.parametrize(
    "wrapped", ["`def solve(xs)`", "`def solve(xs) -> int`.", "def solve(xs)."]
)
def test_a_signature_wrapped_in_markdown_is_read(wrapped):
    """The brief writes the line in backticks, so a model that mirrors them
    has still ended the statement on it."""
    written = read(draft(statement=f"Return ...\n\n{wrapped}"))

    assert parameters(written.statement) == ("xs",)


def test_a_positional_only_canonical_is_the_same_order():
    """A `/` marks how the arguments are passed, and the cases pass them
    positionally either way."""
    written = read(draft(canonical="def solve(xs, /):\n    return len(xs)\n"))

    assert parameters(written.canonical) == ("xs",)


@pytest.mark.parametrize("missing", ["title", "statement", "canonical", "cases", "difficulty"])
def test_a_reply_missing_any_part_fails(missing):
    body = json.loads(draft())
    del body[missing]

    with pytest.raises(ValidationError):
        read(json.dumps(body))


def test_a_draft_carrying_no_case_decides_nothing():
    """A problem does not land without the cases that judge it."""
    with pytest.raises(ValidationError):
        read(draft(cases=[]))


def test_arguments_that_are_not_json_fail_on_arrival():
    """The schema's guarantee ends with the request. Text that does not parse
    is caught here rather than stored as cases nothing can run."""
    with pytest.raises(ValidationError):
        read(draft(cases=[{"args": "[1, 2", "expected": "3"}]))


def test_a_string_expected_keeps_its_quotes():
    """JSON inside a string, so a returned string is a string and not the
    text of a number."""
    assert read(draft(cases=[{"args": "[]", "expected": '"ab"'}])).cases[0].expected == "ab"


def test_the_schema_is_strict():
    """Every property required and none added, which is what the endpoint
    enforces. Anything looser answers with a part missing."""
    shape = schema()
    case = shape["properties"]["cases"]["items"]

    assert sorted(shape["required"]) == sorted(shape["properties"])
    assert shape["additionalProperties"] is False
    assert sorted(case["required"]) == sorted(case["properties"])
    assert case["additionalProperties"] is False


def test_a_case_without_an_expected_return_fails():
    """`None` is a value a solution may return, so absence cannot stand in for
    it — the same rule `TestCase` holds."""
    with pytest.raises(ValidationError):
        read(draft(cases=[{"args": "[]"}]))


@dataclass
class FakeModel:
    """Records the request rather than making one, and answers with whatever
    the test wrote."""

    text: str | None
    calls: list[dict] = field(default_factory=list)

    def __call__(self, **kwargs) -> Reply:
        self.calls.append(kwargs)
        return Reply(text=self.text, stop_reason="stop" if self.text else "length")


def written(tmp_path, model: FakeModel, **overrides):
    (one,) = seeded(tmp_path, card())
    return generate(model, CallLog(tmp_path), one, one.templates[0], **overrides)


def test_one_call_carries_all_three_parts(tmp_path):
    """Cases asked for in a second call describe the solution that already
    exists, so the brief and the schema go out together."""
    model = FakeModel(draft())

    result, call = written(tmp_path, model)

    assert len(model.calls) == 1
    assert model.calls[0]["schema"] == schema()
    assert "Template: longest-valid-window" in model.calls[0]["content"]
    assert result.canonical.startswith("def solve")
    assert call.prompt_hash == prompt_hash(SYSTEM, model.calls[0]["content"])


def test_generation_is_sampled_at_the_provider_default(tmp_path):
    """The exception to the greedy rule: generation makes an artifact rather
    than a verdict, and variance is what stops one model's habits becoming the
    whole corpus.

    Left to the provider rather than set here. A model reasoning at an effort
    accepts no temperature, and its endpoint drops the request the moment one
    is sent. Recorded absent, which is equal only to itself.
    """
    model = FakeModel(draft())

    _, call = written(tmp_path, model)

    assert model.calls[0]["temperature"] is None
    assert call.temperature is None


def test_the_configuration_is_what_goes_out(tmp_path):
    """Its own, since generation asks for an artifact where a reading asks for
    a verdict."""
    model = FakeModel(draft())

    written(
        tmp_path,
        model,
        configuration=Configuration(model="a-writer", effort="medium", pin="somewhere/fp8"),
    )

    assert model.calls[0]["model"] == "a-writer"
    assert model.calls[0]["pin"] == "somewhere/fp8"


def test_an_answer_cut_short_writes_no_draft(tmp_path):
    """A reply with no text wrote nothing. The call is recorded as the failure
    it is, and nothing downstream sees a problem."""
    model = FakeModel(None)

    with pytest.raises(GenerationError):
        written(tmp_path, model)

    assert len(CallLog(tmp_path).all()) == 1


def test_the_draft_says_how_hard_the_problem_is():
    """A card's selector filters on it and a ladder's rungs are ordered by it,
    so nothing else would write it."""
    assert read(draft()).difficulty is ProblemDifficulty.MEDIUM
    assert schema()["properties"]["difficulty"]["enum"] == ["easy", "medium", "hard"]


def test_a_difficulty_outside_the_vocabulary_fails():
    """The enum constrains the request; this is the same check on arrival."""
    with pytest.raises(ValidationError):
        read(draft(difficulty="trivial"))


def test_what_the_form_already_has_is_in_the_brief(tmp_path):
    """A model that cannot see them writes the problem the form suggests,
    which is the same problem every run."""
    (one,) = seeded(tmp_path, card())
    content = prompt(one, one.templates[0], ["A first statement.", "A second one."])

    assert "Already written for this form:" in content
    assert "<written>\nA first statement.\n</written>" in content
    assert "<written>\nA second one.\n</written>" in content


def test_a_form_with_nothing_written_carries_no_heading(tmp_path):
    (one,) = seeded(tmp_path, card())

    assert "Already written" not in prompt(one, one.templates[0])


def test_the_brief_asks_for_a_different_question(tmp_path):
    """A new setting for the same question is a variant, and ten variants of
    one problem teach the form once."""
    rule = " ".join(SYSTEM.split())

    assert "Yours asks a different question." in rule


def test_written_statements_reach_the_call(tmp_path):
    model = FakeModel(draft())

    written(tmp_path, model, written=["An earlier statement."])

    assert "An earlier statement." in model.calls[0]["content"]


def test_the_statements_are_the_template_s_own(tmp_path):
    """Every status, retired included: a repeat of a telegraphed problem is
    still the same problem."""
    (one,) = seeded(tmp_path, card())
    mine, theirs = one.templates[0], one.templates[1]
    corpus = [
        Problem(id="p1", title="p1", statement="Mine.", **PROVENANCE, generated_for=mine.id),
        Problem(
            id="p2",
            title="p2",
            statement="Retired but mine.",
            status=ProblemStatus.RETIRED,
            retired_reason=RetirementReason.TELEGRAPHED,
            **PROVENANCE,
            generated_for=mine.id,
        ),
        Problem(id="p3", title="p3", statement="Theirs.", **PROVENANCE, generated_for=theirs.id),
    ]

    assert written_for(corpus, mine) == ["Mine.", "Retired but mine."]
