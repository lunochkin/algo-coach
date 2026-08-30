"""What one generation call is briefed with: a template, its cue, and the
technique it belongs to."""

from matching import card, seeded, template

from algo_coach.generation import SYSTEM, prompt


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
