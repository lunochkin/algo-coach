import json

import pytest
from authoring import LESSON, found, question, written
from commands import run_cli

from algo_coach.knowledge.authoring import check, snippets


def output(qid: str, code: str, **fields) -> dict:
    return question(qid, kind="output", code=code, **fields)


def ran(root, **flags):
    return check(root, other_versions=False, **flags).report


def lesson(text: str) -> dict:
    return {"les": (["sub@0"], LESSON + "\n" + text)}


def test_a_snippet_printing_an_unkeyed_choice_is_refused(tmp_path):
    """Rule 1: the snippet prints `two`, and `one` is keyed."""
    root = written(tmp_path, [output("a", "print('two')")])

    assert any("matches an unkeyed choice" in e for e in found(ran(root).errors, 1))


def test_a_snippet_printing_no_choice_is_warned(tmp_path):
    """Rule 1: the printed line is in none of the choices."""
    root = written(tmp_path, [output("a", "print('seven')")])

    assert any("matches no choice" in w for w in found(ran(root).warnings, 1))


def test_a_snippet_the_skip_list_names_is_not_run(tmp_path):
    """Rule 1's skip list holds a snippet that cannot run as shown."""
    root = written(
        tmp_path, [output("a", "print('two')")], check='[skip.snippet]\na = "needs a debugger"\n'
    )

    assert found(ran(root).errors, 1) == []


def test_a_short_answer_is_the_real_output(tmp_path):
    """Rule 3: the snippet prints 5, and only 6 is accepted."""
    short = output("a", "print(2 + 3)", format="short", accept=["6"])
    root = written(tmp_path, [short])

    assert any("matches no accepted answer" in e for e in found(ran(root).errors, 3))


def test_an_accepted_spelling_passes(tmp_path):
    """Rule 3: `accept` covers the reply with and without quotes."""
    short = output("a", "print('ab')", format="short", accept=["'ab'"])
    root = written(tmp_path, [short])

    assert found(ran(root).errors, 3) == []


@pytest.mark.parametrize("fence", ["output", "text"])
def test_a_lesson_block_matches_its_shown_output(tmp_path, fence):
    """Rule 2: the block prints 1 and shows 2, fenced either way until the
    content repository refences its output."""
    text = f"```python\nprint(1)\n```\n```{fence}\n2\n```\n"
    root = written(tmp_path, [question("a")], lessons=lesson(text))

    assert any("shown '2', got '1'" in e for e in found(ran(root).errors, 2))


def test_a_block_needing_an_earlier_one_is_warned(tmp_path):
    """Rule 2: a reader may jump to any section, so a block carries its own
    names."""
    text = "```python\nx = 41\n```\n\n```python\nprint(x + 1)\n```\n```text\n42\n```\n"
    root = written(tmp_path, [question("a")], lessons=lesson(text))

    assert found(ran(root).warnings, 2) == [
        "[2] lessons/les.md block 2: runs only after the lesson's earlier blocks"
    ]


def test_a_postgres_block_needs_a_test_server(tmp_path, monkeypatch):
    """Rule 2: a Postgres block runs on a database of its own, so with no
    server it fails rather than passing unrun."""
    monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
    text = '```python\nimport psycopg\npsycopg.connect("dbname=app")\n```\n'
    root = written(tmp_path, [question("a")], lessons=lesson(text))

    assert any("set TEST_DATABASE_URL" in e for e in found(ran(root).errors, 2))


def test_a_tool_output_is_what_the_tool_prints(tmp_path):
    """Rule 4: ruff's report under a block, with a line ruff does not print."""
    shown = "$ ruff check ex.py\nex.py:9:8: F401 [*] `os` imported but unused\n"
    root = written(
        tmp_path,
        [question("a")],
        lessons=lesson(f"```python\nimport os\n```\n```text\n{shown}```\n"),
    )

    assert any("which the tool does not print" in e for e in found(ran(root).errors, 4))


def test_a_transcript_is_replayed_against_the_tool(tmp_path):
    """Rule 4: a console transcript's `cat` writes the file its `ruff` reads."""
    shown = "$ cat ex.py\nimport os\n$ ruff check ex.py\nex.py:3:8: F401 nothing\n"
    root = written(tmp_path, [question("a")], lessons=lesson(f"```console\n{shown}```\n"))

    errors = found(ran(root).errors, 4)

    assert any("`ruff check ex.py` shows" in e for e in errors)


def test_a_transcript_reading_an_unshown_file_is_not_replayed(tmp_path):
    """Rule 4: nothing can be compared, and the report says so."""
    shown = "$ ruff check gone.py\ngone.py:1:1: F401 x\n"
    root = written(tmp_path, [question("a")], lessons=lesson(f"```console\n{shown}```\n"))

    assert ran(root).unreplayed == ["lessons/les.md transcript 1"]


@pytest.fixture
def other(tmp_path, monkeypatch):
    """An interpreter standing for another supported version, which prints
    whatever the test says. Every run of it prints the same line."""

    def interpreter(prints: str) -> None:
        fake = tmp_path / "other-python"
        fake.write_text(f"#!/bin/sh\necho {prints}\n")
        fake.chmod(0o755)
        monkeypatch.setattr(snippets, "find", lambda _spec, _report: str(fake))

    return interpreter


def test_a_snippet_printing_otherwise_on_an_older_version_names_it(tmp_path, other):
    """Rule 5: the output differs on 3.13, under a prompt naming no version."""
    other("other")
    root = written(tmp_path, [output("a", "print('one')")], check='versions = ["3.13"]\n')

    errors = found(check(root).report.errors, 5)

    assert errors == [
        "[5] banks/t/sub.toml a: prints something else on 3.13, and the prompt names no version"
    ]


def test_a_version_named_where_nothing_differs_is_warned(tmp_path, other):
    """Rule 5: a version tag on behaviour identical across the range."""
    other("one")
    root = written(
        tmp_path,
        [output("a", "print('one')", prompt="On 3.13, what prints?")],
        check='versions = ["3.13"]\n',
    )

    assert any("same on every supported version" in w for w in check(root).report.warnings)


def test_a_snippet_printing_otherwise_on_the_free_threaded_build_is_warned(tmp_path, other):
    """Rule 5: the prompt names no build."""
    other("other")
    root = written(tmp_path, [output("a", "print('one')")], check='builds = ["3.15t"]\n')

    assert any("free-threaded 3.15t" in w for w in check(root).report.warnings)


def test_an_answer_keyed_for_another_build_is_what_it_prints(tmp_path, other):
    """Rule 5: check.toml's `expect` holds what that build prints."""
    other("other")
    root = written(tmp_path, [output("a", "print('one')")], check='[expect."3.15t"]\na = "three"\n')

    assert any("expects 'three' on 3.15t" in e for e in check(root).report.errors)


def test_a_kept_result_is_not_run_again(tmp_path):
    """The cache beside the module answers an unchanged snippet."""
    root = written(tmp_path, [output("a", "print('one')")])
    first = check(root, other_versions=False)

    again = check(root, other_versions=False)

    assert (first.executed, again.executed) == (1, 0)
    assert check(root, other_versions=False, fresh=True).executed == 1


def test_the_command_prints_the_findings_and_fails_on_an_error(tmp_path, monkeypatch, capsys):
    """`algo-coach module check` exits 1 where a rule refused something."""
    written(tmp_path, [question("a", answer=["A", "B"])])

    with pytest.raises(SystemExit) as exit:
        run_cli(monkeypatch, "module", "check", "m", "--content", "modules", "--no-run")

    assert exit.value.code == 1
    assert capsys.readouterr().out.splitlines() == [
        "error   [8] banks/t/sub.toml a: choose 2 of 3",
        "1 errors, 0 warnings",
    ]


def test_the_command_reports_as_json(tmp_path, monkeypatch, capsys):
    """`--json` carries what the summary line counts."""
    written(tmp_path, [output("a", "print('one')")])

    run_cli(monkeypatch, "module", "check", "m", "--content", "modules", "--json", "--no-versions")

    report = json.loads(capsys.readouterr().out)
    assert (report["errors"], report["ran"]["snippets"]) == ([], 1)


def test_the_command_lists_near_pairs_and_stops(tmp_path, monkeypatch, capsys):
    """`--near` runs no rule."""
    written(tmp_path, [question("a", answer=["A", "B"])])

    run_cli(monkeypatch, "module", "check", "m", "--content", "modules", "--near")

    assert capsys.readouterr().out == ""


def test_the_command_refuses_a_directory_holding_no_module(tmp_path, monkeypatch):
    """A slug naming nothing is a usage error, not an empty pass."""
    with pytest.raises(SystemExit) as exit:
        run_cli(monkeypatch, "module", "check", "gone")

    assert exit.value.code == 2
