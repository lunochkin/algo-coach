from authoring import LESSON, _bank, found, git, question, rebanked, written

from algo_coach.knowledge.authoring import check, in_sub, load, near


def checked(root, **flags):
    return check(root, run=False, **flags).report


def test_a_module_holding_every_rule_reports_nothing(tmp_path):
    """The fixture itself breaks no rule, so a finding below is the one its
    test arranged."""
    report = check(written(tmp_path, [question("a")])).report

    assert (report.errors, report.warnings) == ([], [])


def test_a_kind_the_module_does_not_name_is_refused(tmp_path):
    """The seed's refusal, caught before a seed: a kind outside `kinds`, and
    a code kind with no code."""
    root = written(tmp_path, [question("a", kind="trivia"), question("b", kind="debug")])

    errors = found(checked(root).errors, 1)

    assert any("kind 'trivia'" in e for e in errors)
    assert any("debug question carries no code" in e for e in errors)


def test_a_version_the_prompt_names_is_the_installed_one(tmp_path):
    """Rule 6: pytest 1.0 in a prompt, with pytest 9 installed."""
    root = written(tmp_path, [question("a", prompt="Under pytest 1.0, what runs?")])

    assert any("prompt names pytest 1.0" in e for e in found(checked(root).errors, 6))


def test_a_version_check_toml_skips_is_not_compared(tmp_path):
    """Rule 6's skip list holds a version that is the scenario's own."""
    root = written(
        tmp_path,
        [question("a", prompt="Under pytest 1.0, what runs?")],
        check='[skip.library-version]\na = "the scenario pins it"\n',
    )

    assert found(checked(root).errors, 6) == []


def test_choosing_all_but_one_option_is_refused(tmp_path):
    """Rule 8: choose 2 of 3 leaves one wrong option to spot."""
    root = written(tmp_path, [question("a", answer=["A", "B"])])

    assert found(checked(root).errors, 8) == ["[8] banks/t/sub.toml a: choose 2 of 3"]


def test_a_keyed_choice_far_longer_than_the_rest_is_warned(tmp_path):
    """Rule 10: the answer recognisable by its length."""
    root = written(tmp_path, [question("a", choices=["x" * 60, "short", "brief"])])

    assert found(checked(root).warnings, 10) != []


def test_prose_naming_a_choice_by_position_is_refused(tmp_path):
    """Rule 10: the choices are shuffled, so `the first choice` names none."""
    root = written(tmp_path, [question("a", explain="As the first choice says.")])

    assert any("the first choice" in e for e in found(checked(root).errors, 10))


def test_an_open_question_holds_three_or_four_points_readable_alone(tmp_path):
    """Rule 13: a count outside three to four, and a point leaning on one."""
    two = question("a", format="card", key=["one point", "another point"])
    leaning = question("b", format="card", key=["A first point", "It is so", "A third one"])
    root = written(tmp_path, [two, leaning])

    errors = found(checked(root).errors, 13)

    assert any("a: 2 key points" in e for e in errors)
    assert any("b: point leans on another" in e for e in errors)


def _alike(n: int) -> list[dict]:
    """Questions explained in words of their own, and two explained alike. A
    word counts toward likeness only where few questions use it."""
    own = [
        question(f"q{i}", explain=f"word{i}a word{i}b word{i}c", detail={"mechanism": f"m{i}x"})
        for i in range(n)
    ]
    same = {"explain": "descriptors bind getattr lookups", "detail": {"mechanism": "binding"}}
    return [*own, question("x", **same), question("y", **same)]


def test_two_questions_explained_alike_are_warned(tmp_path):
    """Rule 14: one fact asked twice reads as two explanations alike."""
    root = written(tmp_path, _alike(20))

    assert any(w.startswith("[14] x ~ y: explained alike") for w in checked(root).warnings)


def test_a_pair_skip_same_fact_names_is_not_warned(tmp_path):
    """Rule 14: a pair recorded as asking two facts."""
    root = written(tmp_path, _alike(20), check='[skip.same-fact]\n"x ~ y" = "two facts"\n')

    assert found(checked(root).warnings, 14) == []


def test_near_lists_the_pairs_most_alike_for_one_id(tmp_path):
    """`--near x` names x first, then the question explained most like it."""
    root = written(tmp_path, _alike(20))

    assert near(load(root), "x")[0].endswith("x (sub L0)  ~  y (sub L0)")


def test_two_near_identical_snippets_are_warned(tmp_path):
    """Rule 14: a snippet copied into a second question."""
    code = "values = [3, 1, 2]\nvalues.sort(key=lambda v: -v)\nprint(values[0], values[-1])\n"
    root = written(
        tmp_path, [question("a", kind="output", code=code), question("b", kind="output", code=code)]
    )

    assert "[14] a ~ b: near-identical snippets, not in duplicates" in checked(root).warnings


def test_a_lesson_repeating_its_questions_snippet_is_warned(tmp_path):
    """Rule 15: the question then tests recall of a printed line."""
    code = "pairs = dict(zip('abc', range(3)))\nprint(sorted(pairs.items(), reverse=True))\n"
    lesson = LESSON + f"\n```python\n{code}```\n"
    root = written(
        tmp_path,
        [question("a", kind="output", code=code)],
        lessons={"les": (["sub@0"], lesson)},
    )

    assert any("the lesson repeats the snippet" in w for w in found(checked(root).warnings, 15))


def test_a_question_below_its_lessons_level_is_refused(tmp_path):
    """Rule 17: the question would wait on a lesson still locked."""
    root = written(tmp_path, [question("a")], lessons={"les": (["sub@1"], LESSON)})

    assert found(checked(root).errors, 17) == [
        "[17] banks/t/sub.toml a: L0 question in an L1 lesson"
    ]


def test_a_link_to_a_missing_lesson_or_section_is_refused(tmp_path):
    """Rule 18: a link nothing answers."""
    text = LESSON + "\nSee [gone](lesson:gone) and [here](lesson:les#nowhere).\n"
    root = written(tmp_path, [question("a")], lessons={"les": (["sub@0"], text)})

    errors = found(checked(root).errors, 18)

    assert any("links lesson:gone, which does not exist" in e for e in errors)
    assert any("links lesson:les#nowhere" in e for e in errors)


def test_a_section_no_question_points_at_is_warned(tmp_path):
    """Rule 18: retiring questions leaves sections behind."""
    text = LESSON + "\n## Orphan\n\nMore prose.\n\n## Summary\n\nIgnored.\n"
    root = written(tmp_path, [question("a")], lessons={"les": (["sub@0"], text)})

    assert found(checked(root).warnings, 18) == [
        "[18] lessons/les.md: no question points at #orphan"
    ]


def test_a_text_block_drawing_nothing_is_warned(tmp_path):
    """Rule 24: a phone keeps a `text` block whole, so output fenced as
    `text` scrolls sideways where `output` would wrap."""
    drawn = ["┌─┐\n└─┘", "eq=True    unhashable", "x[0]\n ~^^^", "DEBUG < INFO < ERROR"]
    blocks = ["```text\n42\n```", *(f"```text\n{d}\n```" for d in drawn), "```output\n42\n```"]
    text = LESSON + "\n" + "\n\n".join(blocks) + "\n"
    root = written(tmp_path, [question("a")], lessons={"les": (["sub@0"], text)})

    assert found(checked(root).warnings, 24) == [
        "[24] lessons/les.md line 7: a text block draws nothing: fence output as `output`"
    ]


def test_box_drawing_outside_a_text_block_is_refused(tmp_path):
    """Rule 24: a drawing made of box characters scrolls sideways on a
    phone, so it sits in a `text` block or a question's diagram. A tool's
    own output in an `output` or `console` fence may hold them."""
    tree = "├── a\n└── b\n"
    q = question("a", detail={"mechanism": "m", "example": tree, "diagram": tree})
    langs = ("python", "", "text", "output", "console")
    fences = "".join(f"\n```{lang}\n{tree}```\n" for lang in langs)
    root = written(tmp_path, [q], lessons={"les": (["sub@0"], LESSON + "\nA │ B\n" + fences)})

    assert [e.split(": ")[0] for e in found(checked(root).errors, 24)] == [
        "[24] lessons/les.md line 7 of the prose",
        "[24] lessons/les.md line 9",
        "[24] lessons/les.md line 14",
        "[24] banks/t/sub.toml a example",
    ]


def test_a_line_wider_than_a_phone_is_warned(tmp_path):
    """Rule 25: a phone wraps a line past some 40 characters, and a wrap in
    a snippet read for its output can pass for a line break. A `text`
    block is a drawing, kept whole, and a `mermaid` one is drawn to the
    screen's width: neither is counted."""
    wide = "print(" + "x" * 60 + ")\n"
    q = question("a", kind="output", code=wide, detail={"mechanism": "m", "example": wide})
    langs = ("python", "output", "text", "mermaid")
    fences = "".join(f"\n```{lang}\n{wide}```\n" for lang in langs)
    root = written(tmp_path, [q], lessons={"les": (["sub@0"], LESSON + fences)})

    assert found(checked(root).warnings, 25) == [
        "[25] banks/t/sub.toml a code: 1 line over 60 characters, the longest 67",
        "[25] banks/t/sub.toml a example: 1 line over 60 characters, the longest 67",
        "[25] lessons/les.md line 7: 1 line over 60 characters, the longest 67",
        "[25] lessons/les.md line 11: 1 line over 60 characters, the longest 67",
    ]


def test_every_concept_is_covered_and_every_question_filed(tmp_path):
    """Rule 19: a concept with no question at its level, and a question
    under no concept."""
    coverage = (
        '[subtopic.sub]\n[[subtopic.sub.concept]]\nid = "c"\nlevel = 1\ncovered_by = ["a", "z"]\n'
    )
    root = written(tmp_path, [question("a"), question("b")], coverage=coverage)

    assert sorted(found(checked(root).errors, 19)) == [
        "[19] banks/t/sub.toml b: filed under no concept",
        "[19] coverage/t.toml sub/c: no question at L1",
        "[19] coverage/t.toml sub/c: unknown ids ['z']",
    ]


def test_an_id_a_past_commit_retired_is_never_used_again(tmp_path):
    """Rule 21: a reused id attaches the old answers to the new question."""
    root = written(tmp_path, [question("a"), question("b")])
    rebanked(root, [question("a")])
    rebanked(root, [question("a"), question("b")])

    assert found(checked(root).errors, 21) == [
        "[21] banks/t/sub.toml b: reuses an id a past commit retired"
    ]


def test_a_branch_cut_before_an_id_retires_nothing(tmp_path, monkeypatch):
    """Rule 21: a branch merged after `b` was written, though dated later,
    never held `b`, so it removed nothing."""

    def at(day: int) -> None:
        for name in ("GIT_AUTHOR_DATE", "GIT_COMMITTER_DATE"):
            monkeypatch.setenv(name, f"2026-11-{day:02d}T12:00:00")

    at(1)
    root = written(tmp_path, [question("a")])
    git(root, "checkout", "-q", "-b", "side")
    at(3)
    rebanked(root, [question("a"), question("c")])
    git(root, "checkout", "-q", "-")
    at(2)
    (root / "banks" / "t" / "other.toml").write_text(_bank([question("b")]))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "other")
    at(4)
    git(root, "merge", "-q", "--no-edit", "side")

    assert found(checked(root).errors, 21) == []


def test_an_id_used_twice_is_refused(tmp_path):
    """Rule 21, within one module's banks."""
    root = written(tmp_path, [question("a"), question("a")], coverage="")

    assert "[21] a: id used 2 times" in checked(root).errors


def test_a_subtopic_scope_names_its_own_files_alone(tmp_path):
    """`--sub` keeps a finding on the subtopic's bank, question, lesson or
    coverage entry, and leaves another subtopic's."""
    root = written(tmp_path, [question("a")], lessons={"les": (["sub@0"], LESSON)})
    named = in_sub(load(root), "sub")

    assert named("[19] banks/t/sub.toml a: wrong choice C names no misconception")
    assert named("[18] lessons/les.md: no question points at #x")
    assert named("[19] coverage/t.toml sub/c: no question at L0")
    assert named("[21] a: id used 2 times")
    assert not named("[19] banks/t/other.toml b: wrong choice C names no misconception")
    assert not named("[19] coverage/t.toml other/c: no question at L0")
