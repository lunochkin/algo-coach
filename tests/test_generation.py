"""What one generation call is briefed with: a template, its cue, and the
technique it belongs to."""

import json

import pytest
from matching import card, seeded, template
from pydantic import ValidationError

from algo_coach.generation import SYSTEM, prompt, read, schema


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
            "statement": "Given a list of readings, return ...",
            "canonical": "def solve(xs):\n    return len(xs)\n",
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


@pytest.mark.parametrize("missing", ["title", "statement", "canonical", "cases"])
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
