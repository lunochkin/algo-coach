import json
from pathlib import Path

import pytest
from commands import connected, run_cli
from sqlalchemy import select

from algo_coach.knowledge import read_module, refusals, seed_module
from algo_coach.knowledge.table import lessons, modules, questions, subtopics, topics

COURSE = """\
title = "Python"
pass_ratio = 0.8
kinds = ["concept", "output"]
code_kinds = ["output"]
code_lang = "python"

[[topic]]
slug = "core"
tier = 1
title = "Core"
subs = ["types", "flow"]
"""

CHOICE = """\
[[q]]
id = "types-1"
kind = "concept"
level = 0
prompt = "Which is mutable?"
choices = ["tuple", "list", "str"]
answer = "B"
why = ["immutable", "mutable", "immutable"]
explain = "A list changes in place."
lesson = "names#binding"
[q.detail]
mechanism = "A list holds references it can rebind."
"""

OPEN = """\
[[q]]
id = "types-2"
format = "card"
kind = "concept"
level = 1
prompt = "Why does a default list leak between calls?"
key = ["defaults are evaluated once", "the list object is shared"]
traps = ["each call gets a new list"]
lesson = "names"
"""

SHORT = """\
[[q]]
id = "flow-1"
format = "short"
kind = "output"
level = 1
prompt = "What prints?"
code = "print(1 or 2)"
accept = ["1"]
explain = "`or` returns its first truthy operand."
lesson = "names"
[q.detail]
mechanism = "Short-circuit evaluation."
"""

GRAPH = """\
format = 2
[lesson.names]
title = "Names"
file = "lessons/names.md"
teaches = ["types@0"]
"""


def authored(tmp_path: Path, *, types: str = CHOICE + OPEN, flow: str = SHORT) -> Path:
    base = tmp_path / "python"
    (base / "banks" / "core").mkdir(parents=True)
    (base / "lessons").mkdir()
    (base / "course.toml").write_text(COURSE)
    (base / "graph.toml").write_text(GRAPH)
    (base / "lessons" / "names.md").write_text("# Names\n\n## Binding\n\nA name points.\n")
    (base / "banks" / "core" / "types.toml").write_text(types)
    (base / "banks" / "core" / "flow.toml").write_text(flow)
    return base


def rows(database, table):
    with database.connect() as conn:
        return [dict(row) for row in conn.execute(select(table)).mappings()]


def test_a_module_seeds_every_level_of_its_content(database, tmp_path):
    result = seed_module(read_module(authored(tmp_path)), root=database)

    assert result.refused == []
    assert [len(rows(database, t)) for t in (modules, topics, subtopics, questions, lessons)] == [
        1, 1, 2, 3, 1,
    ]  # fmt: skip


def test_learn_s_card_format_is_stored_as_an_open_question(database, tmp_path):
    """`card` collides with a Card here, and the glossary names it `open`."""
    seed_module(read_module(authored(tmp_path)), root=database)

    stored = {row["slug"]: row for row in rows(database, questions)}
    assert stored["types-2"]["format"] == "open"
    assert stored["types-2"]["body"]["key"] == [
        "defaults are evaluated once",
        "the list object is shared",
    ]


def test_the_body_holds_the_format_s_fields_and_no_column(database, tmp_path):
    """A field with a column of its own is stored once, in the column."""
    seed_module(read_module(authored(tmp_path)), root=database)

    body = {row["slug"]: row["body"] for row in rows(database, questions)}["types-1"]
    assert {"id", "kind", "level", "prompt", "lesson", "code", "format"}.isdisjoint(body)
    assert body["answer"] == "B"


def test_a_re_seed_keeps_every_minted_id(database, tmp_path):
    """The log references the ids, so a refresh may never mint them again."""
    source = read_module(authored(tmp_path))
    seed_module(source, root=database)
    first = {row["slug"]: row["id"] for row in rows(database, questions)}

    seed_module(source, root=database)

    assert {row["slug"]: row["id"] for row in rows(database, questions)} == first


def test_a_reworded_question_keeps_its_slug_and_its_id(database, tmp_path):
    seed_module(read_module(authored(tmp_path)), root=database)
    before = {row["slug"]: row["id"] for row in rows(database, questions)}

    reworded = CHOICE.replace("Which is mutable?", "Which of these is mutable?")
    seed_module(read_module(authored(tmp_path / "again", types=reworded + OPEN)), root=database)

    after = {row["slug"]: row for row in rows(database, questions)}
    assert after["types-1"]["id"] == before["types-1"]
    assert after["types-1"]["prompt"] == "Which of these is mutable?"


def test_a_question_gone_from_the_files_is_retired_and_kept(database, tmp_path):
    """`knowledge.md`, Seeding: a deleted row would leave its answers pointing
    at nothing."""
    seed_module(read_module(authored(tmp_path)), root=database)

    result = seed_module(read_module(authored(tmp_path / "again", types=CHOICE)), root=database)

    stored = {row["slug"]: row for row in rows(database, questions)}
    assert stored["types-2"]["retired_at"] is not None
    assert stored["types-1"]["retired_at"] is None
    assert result.retired == 1


def test_a_retired_slug_is_never_reused(database, tmp_path):
    """A reused slug would attach the old answers to whatever question took
    it."""
    seed_module(read_module(authored(tmp_path)), root=database)
    seed_module(read_module(authored(tmp_path / "gone", types=CHOICE)), root=database)

    result = seed_module(read_module(authored(tmp_path / "back")), root=database)

    assert result.refused == ["types-2: a retired slug is never reused"]


@pytest.mark.parametrize(
    ("types", "refusal"),
    [
        (CHOICE.replace('prompt = "Which is mutable?"\n', ""), "missing ['prompt']"),
        (CHOICE + CHOICE, "duplicate id"),
        (CHOICE.replace('"concept"', '"trivia"'), "kind 'trivia' not in course kinds"),
        (CHOICE.replace('answer = "B"', 'answer = "D"'), "bad answer 'D'"),
        (OPEN.replace(', "the list object is shared"', ""), "key must be a list of 2-6"),
        (CHOICE.replace("names#binding", "names#nowhere"), "no section #nowhere in lesson names"),
        (CHOICE.replace("level = 0", "level = 4"), "bad level 4"),
    ],
)
def test_the_seed_refuses_what_learn_s_check_refused(tmp_path, types, refusal):
    found = refusals(read_module(authored(tmp_path, types=types)))

    assert any(refusal in one for one in found), found


def test_a_refused_module_writes_nothing(database, tmp_path):
    """A module is checked whole, as `learn check` checked a course, so a seed
    never stores half of one."""
    broken = CHOICE.replace('answer = "B"', 'answer = "D"')

    result = seed_module(read_module(authored(tmp_path, types=broken)), root=database)

    assert result.refused and rows(database, questions) == []


def test_a_bank_the_course_does_not_list_is_refused(tmp_path):
    base = authored(tmp_path)
    (base / "banks" / "core" / "stray.toml").write_text(CHOICE.replace("types-1", "stray-1"))

    assert "core/stray: not in course.toml" in refusals(read_module(base))


def test_the_terminal_seeds_a_module(database, tmp_path, monkeypatch, capsys):
    connected(database, monkeypatch)

    run_cli(monkeypatch, "seed", "knowledge", str(authored(tmp_path)))

    assert json.loads(capsys.readouterr().out)["questions"] == 3
