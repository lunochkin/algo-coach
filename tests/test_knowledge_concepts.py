from pathlib import Path

from algo_coach.knowledge import read_module

COURSE = """title = "M"
kinds = ["principle"]

[[topic]]
slug = "core"
tier = 1
subs = ["flow"]
"""
GRAPH = """[lesson.flow-loops]
title = "Loops"
file = "lessons/flow-loops.md"
teaches = ["flow@0"]
"""
CONCEPTS = """[[concept]]
id = "while-retests"
level = 0
claim = "`while` tests its condition before every iteration."
source = "https://docs.python.org/3/reference/compound_stmts.html#the-while-statement"
misconceptions = [{ id = "body-runs-once", text = "A `while` body always runs once." }]
taught_by = "flow-loops#while"
"""
QUESTION = """[[q]]
id = "w-zero"
kind = "principle"
concept = "while-retests"
prompt = "How often does the body run?"
choices = ["never", "once", "twice"]
answer = ["A"]
why = ["a", "b", "c"]
"""


def module(tmp_path: Path, bank: str = QUESTION, concepts: str = CONCEPTS) -> Path:
    base = tmp_path / "m"
    for sub in ("banks/core", "concepts/core", "lessons"):
        (base / sub).mkdir(parents=True)
    (base / "course.toml").write_text(COURSE)
    (base / "graph.toml").write_text(GRAPH)
    (base / "lessons" / "flow-loops.md").write_text("## `while`\n\nProse.\n")
    (base / "concepts" / "core" / "flow.toml").write_text(concepts)
    (base / "banks" / "core" / "flow.toml").write_text(bank)
    return base


def test_a_question_takes_its_lesson_level_and_detail_from_its_concept(tmp_path):
    """The concept holds the fact once; the question carries none of it."""
    source = read_module(module(tmp_path))

    raw = source.banks[0].questions[0]
    assert source.unread == []
    assert raw["lesson"] == "flow-loops#while"
    assert raw["level"] == 0
    assert raw["detail"] == {
        "mechanism": "`while` tests its condition before every iteration.",
        "pitfalls": ["A `while` body always runs once."],
    }


def test_a_question_naming_an_unknown_concept_is_unread(tmp_path):
    """A typo in `concept` would otherwise seed a question with no lesson."""
    source = read_module(module(tmp_path, QUESTION.replace("while-retests", "nope")))

    assert source.unread == ["core/flow:w-zero: unknown concept nope"]


def test_a_question_restating_a_derived_field_is_unread(tmp_path):
    """A copy of the concept's field in the question drifts from the concept."""
    bank = QUESTION + 'lesson = "flow-loops#while"\n'

    source = read_module(module(tmp_path, bank))

    assert source.unread == ["core/flow:w-zero: lesson is derived from concept while-retests"]


def test_a_lesson_gets_its_intro_mistakes_and_links_from_its_concepts(tmp_path):
    """The seed renders what a hand-written copy would let drift."""
    text = read_module(module(tmp_path)).lesson_texts["flow-loops"]

    assert text.startswith("This lesson covers `while`.\n\n## `while`")
    assert "## Common mistakes\n\n- Wrong: A `while` body always runs once.\n" in text
    assert "(https://docs.python.org/3/reference/compound_stmts.html#the-while-statement)" in text


def test_a_choice_naming_an_unknown_misconception_is_unread(tmp_path):
    """A misconception removed from the concept leaves no choice pointing at
    nothing: the reading refuses the question until it is rewritten."""
    bank = QUESTION + 'misconception = { B = "gone" }\n'

    source = read_module(module(tmp_path, bank))

    assert source.unread == ["core/flow:w-zero: no misconception gone in concept while-retests"]


def test_a_module_without_concepts_reads_as_before(tmp_path):
    """`python` has no concept files, and its lessons stay as written."""
    base = module(tmp_path)
    for path in (base / "concepts" / "core").iterdir():
        path.unlink()

    source = read_module(base)

    assert source.lesson_texts["flow-loops"] == "## `while`\n\nProse.\n"


def test_a_concept_with_two_sources_links_both(tmp_path):
    """One section may not cover every clause of a claim."""
    two = CONCEPTS.replace(
        'source = "https://docs.python.org/3/reference/compound_stmts.html#the-while-statement"',
        'source = ["https://docs.python.org/3/reference/compound_stmts.html#the-while-statement",'
        ' "https://docs.python.org/3/library/sys.html#sys.getrecursionlimit"]',
    )

    text = read_module(module(tmp_path, concepts=two)).lesson_texts["flow-loops"]

    assert "(https://docs.python.org/3/library/sys.html#sys.getrecursionlimit)" in text


def test_a_choice_may_name_another_concepts_misconception(tmp_path):
    """A wrong choice can embody a belief another concept holds."""
    other = CONCEPTS + CONCEPTS.replace('id = "while-retests"', 'id = "for-each"').replace(
        'id = "body-runs-once"', 'id = "skips-last"'
    )
    bank = QUESTION + 'misconception = { B = "for-each#skips-last" }\n'

    source = read_module(module(tmp_path, bank, concepts=other))

    assert source.unread == []


def test_a_choice_naming_an_unknown_concepts_misconception_is_unread(tmp_path):
    """`concept#id` resolves like an id of the question's own concept."""
    bank = QUESTION + 'misconception = { B = "nope#x" }\n'

    source = read_module(module(tmp_path, bank))

    assert source.unread == ["core/flow:w-zero: no misconception x in concept nope"]
