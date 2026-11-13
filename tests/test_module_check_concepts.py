import json
from pathlib import Path

from authoring import found, written

from algo_coach.knowledge.authoring import check

LESSON = "## While\n\n`while` tests its condition first.\n"


def concept(**fields) -> dict:
    return {
        "id": "while-retests",
        "level": 0,
        "claim": "`while` tests its condition before every iteration.",
        "source": "https://docs.python.org/3/reference/compound_stmts.html#the-while-statement",
        "witness": "n = 0\nwhile n > 0:\n    print('body')\nprint('done')\n",
        "output": "done\n",
        "misconceptions": [{"id": "body-runs-once", "text": "A `while` body always runs once."}],
        "taught_by": "les#while",
    } | fields


def asking(name: str = "while-retests") -> dict:
    return {
        "id": "w",
        "kind": "concept",
        "concept": name,
        "prompt": "How often does the body run?",
        "choices": ["never", "once", "twice"],
        "answer": ["A"],
        "explain": "The condition is false first.",
        "why": ["a", "b", "c"],
        "misconception": {"B": "body-runs-once", "C": "body-runs-once"},
    }


def module(tmp_path: Path, *concepts: dict, lesson: str = LESSON, q: dict | None = None) -> Path:
    root = written(tmp_path, [q or asking()], lessons={"les": (["sub@0"], lesson)}, coverage="")
    (root / "concepts" / "t").mkdir(parents=True)
    body = ""
    for one in concepts or (concept(),):
        body += "[[concept]]\n" + "".join(f"{k} = {_toml(v)}\n" for k, v in one.items())
    (root / "concepts" / "t" / "sub.toml").write_text(body)
    return root


def _toml(value) -> str:
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{k} = {_toml(v)}" for k, v in value.items()) + " }"
    if isinstance(value, list):
        return "[" + ", ".join(_toml(v) for v in value) + "]"
    return json.dumps(value)


def test_a_module_written_by_concept_holding_every_rule_reports_nothing(tmp_path):
    """The fixture breaks no rule, so each finding below is its test's own."""
    report = check(module(tmp_path), other_versions=False).report

    assert (report.errors, report.warnings) == ([], [])


def test_a_witness_printing_another_output_is_refused(tmp_path):
    """Rule 26: the claim rests on what the witness prints."""
    root = module(tmp_path, concept(output="body\ndone\n"))

    errors = found(check(root, other_versions=False).report.errors, 26)

    assert errors == [
        "[26] concepts/t/sub.toml while-retests: witness prints 'done' on the project's "
        "interpreter, where the concept shows 'body\\ndone'"
    ]


def test_a_concept_with_neither_a_witness_nor_a_quote_is_refused(tmp_path):
    """Rule 27: a claim nothing checks."""
    bare = {k: v for k, v in concept().items() if k not in ("witness", "output")}

    errors = found(check(module(tmp_path, bare), run=False).report.errors, 27)

    assert errors == ["[27] concepts/t/sub.toml while-retests: neither a witness nor a quote"]


def test_a_question_naming_an_unknown_concept_is_refused(tmp_path):
    """Rule 27: the reading's own finding, reported by the check."""
    errors = found(check(module(tmp_path, q=asking("nope")), run=False).report.errors, 27)

    assert errors == ["[27] banks/t/sub.toml:w: unknown concept nope"]


def test_a_lesson_section_teaching_no_concept_is_refused(tmp_path):
    """Rule 28: a section asserting what no witness checks."""
    root = module(tmp_path, lesson=LESSON + "\n## Loops\n\nMore.\n")

    errors = found(check(root, run=False).report.errors, 28)

    assert errors == ["[28] lessons/les.md: #loops teaches no concept"]


def test_a_hand_written_intro_or_mistakes_section_is_refused(tmp_path):
    """Rule 28: the seed renders both, and a copy drifts."""
    root = module(tmp_path, lesson="Loops repeat.\n\n" + LESSON + "\n## Common mistakes\n\n- x\n")

    errors = found(check(root, run=False).report.errors, 28)

    assert any("holds an intro" in e for e in errors)
    assert any("#common-mistakes" in e for e in errors)


def test_a_taught_by_naming_no_section_is_refused(tmp_path):
    """Rule 28: a concept no lesson teaches."""
    root = module(tmp_path, concept(taught_by="les#until"))

    errors = found(check(root, run=False).report.errors, 28)

    assert any("taught_by les#until names no section" in e for e in errors)


def test_a_sentence_opening_with_both_is_warned(tmp_path):
    """Rule 29: an opener the writing rules forbid."""
    root = module(tmp_path, concept(claim="Both loops test first. They stop on false."))

    warnings = found(check(root, run=False).report.warnings, 29)

    assert any("opens with 'Both'" in w for w in warnings)


def test_a_question_naming_no_concept_is_refused_where_concepts_file_questions(tmp_path):
    """Rule 19: in a module written by concept, a question is filed by its
    concept, and the coverage map is not read."""
    loose = asking() | {"lesson": "les#while", "level": 0, "detail": {"mechanism": "Tests first."}}
    del loose["concept"]

    errors = found(check(module(tmp_path, q=loose), run=False).report.errors, 19)

    assert errors == ["[19] banks/t/sub.toml w: names no concept"]


def test_a_misconception_no_wrong_choice_embodies_is_warned(tmp_path):
    """Rule 19: a known wrong belief no question tests."""
    second = {"id": "stops-mid-body", "text": "A `while` loop stops mid-body."}
    root = module(tmp_path, concept(misconceptions=[*concept()["misconceptions"], second]))

    warnings = found(check(root, run=False).report.warnings, 19)

    assert any("misconception stops-mid-body" in w for w in warnings)


def test_a_keyed_choice_naming_a_misconception_is_refused(tmp_path):
    """Rule 19: the right answer embodies no wrong belief."""
    q = asking() | {"misconception": {"A": "body-runs-once", "B": "body-runs-once"}}

    errors = found(check(module(tmp_path, q=q), run=False).report.errors, 19)

    assert any("keyed choice A names a misconception" in e for e in errors)


def test_two_misconceptions_sharing_an_id_are_refused(tmp_path):
    """Rule 27: a choice naming the id could mean either belief."""
    twice = [{"id": "x", "text": "One."}, {"id": "x", "text": "Two."}]

    errors = found(
        check(module(tmp_path, concept(misconceptions=twice)), run=False).report.errors, 27
    )

    assert any("share an id" in e for e in errors)


def test_a_short_reply_of_only_true_or_false_is_refused(tmp_path):
    """Rule 3: a reply with even odds is guessed, not recalled."""
    q = {k: v for k, v in asking().items() if k not in ("choices", "answer", "why")}
    q |= {"format": "short", "accept": ["True", "true"]}
    del q["misconception"]

    errors = found(check(module(tmp_path, q=q), run=False).report.errors, 3)

    assert errors == ["[3] banks/t/sub.toml w: the reply is a yes or no, so the format is choice"]


def test_a_question_sharing_a_name_with_its_section_is_warned(tmp_path):
    """Rule 15: a renamed copy keeps a name of the section's example."""
    lesson = "## While\n\n```python\nfuel = 7\nwhile fuel > 4:\n    fuel = fuel - 1\n```\n"
    q = asking() | {"kind": "output", "code": "fuel = 9\nprint(fuel > 4, 'start')\n"}

    warnings = found(check(module(tmp_path, lesson=lesson, q=q), run=False).report.warnings, 15)

    assert warnings == ["[15] banks/t/sub.toml w: shares fuel with les#while"]


def test_a_keyword_argument_or_a_builtin_shared_with_the_section_is_not_warned(tmp_path):
    """Rule 15: `start=` and `enumerate` are the API the section teaches."""
    lesson = "## While\n\n```python\nfor i, w in enumerate(ws, start=1):\n    print(i)\n```\n"
    q = asking() | {"kind": "output", "code": "print(list(enumerate('ab', start=5)))\n"}

    warnings = found(check(module(tmp_path, lesson=lesson, q=q), run=False).report.warnings, 15)

    assert warnings == []
