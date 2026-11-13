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
        "misconceptions": ["A `while` body always runs once."],
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
    }


def module(tmp_path: Path, *concepts: dict, lesson: str = LESSON, q: dict | None = None) -> Path:
    root = written(tmp_path, [q or asking()], lessons={"les": (["sub@0"], lesson)}, coverage="")
    (root / "concepts" / "t").mkdir(parents=True)
    body = ""
    for one in concepts or (concept(),):
        body += "[[concept]]\n" + "".join(f"{k} = {json.dumps(v)}\n" for k, v in one.items())
    (root / "concepts" / "t" / "sub.toml").write_text(body)
    return root


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
