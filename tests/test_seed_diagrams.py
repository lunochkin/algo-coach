from pathlib import Path

import pytest
from test_seed_knowledge import CHOICE, OPEN, authored, rows

from algo_coach.knowledge import diagrams as drawing
from algo_coach.knowledge import read_module, seed_module
from algo_coach.knowledge.diagrams import DrawError, MermaidCli, mermaid_sources, source_hash
from algo_coach.knowledge.table import diagrams, modules

FLOW = "flowchart TB\n  a --> b"
TREE = "flowchart TB\n  root --> leaf"

FENCED = f"```mermaid\n{FLOW}\n```\n"
LESSON = f"# Names\n\n## Binding\n\n{FENCED}\nA name points.\n\n{FENCED}"

DRAWN = CHOICE + f"diagram = '''\n```mermaid\n{TREE}\n```\n'''\n" + OPEN


class Fake:
    def __init__(self, tool: str = "v1", fail: str | None = None):
        self.tool = tool
        self.fail = fail
        self.drawn: list[list[str]] = []

    def version(self) -> str:
        if self.fail:
            raise DrawError(self.fail)
        return self.tool

    def draw(self, sources: list[str]) -> list[tuple[str, str]]:
        self.drawn.append(sources)
        return [(f"<svg>{one} light</svg>", f"<svg>{one} dark</svg>") for one in sources]


def module(tmp_path: Path, *, types: str = DRAWN, lesson: str = LESSON) -> Path:
    base = authored(tmp_path, types=types)
    (base / "lessons" / "names.md").write_text(lesson)
    return base


def test_the_sources_are_a_lesson_s_fences_and_a_question_s_whole_diagram(tmp_path):
    """Each source counts once, and the newline ending it is dropped, as a
    client's markdown parser drops it before looking the drawing up."""
    assert mermaid_sources(read_module(module(tmp_path))) == [FLOW, TREE]


def test_a_diagram_holding_prose_beside_its_fence_is_no_source(tmp_path):
    """A question's diagram is Mermaid only where the fence is all it holds."""
    types = CHOICE + f"diagram = '''\nAs drawn:\n```mermaid\n{TREE}\n```\n'''\n" + OPEN
    assert mermaid_sources(read_module(module(tmp_path, types=types))) == [FLOW]


def test_the_seed_stores_each_source_s_light_and_dark_drawing(database, tmp_path):
    """The snapshot later reads both schemes from this one row."""
    result = seed_module(read_module(module(tmp_path)), root=database, drawer=Fake())

    stored = {row["source"]: row for row in rows(database, diagrams)}
    assert result.diagrams == 2
    assert stored[TREE]["source_hash"] == source_hash(TREE)
    assert (stored[TREE]["light"], stored[TREE]["dark"], stored[TREE]["tool"]) == (
        f"<svg>{TREE} light</svg>",
        f"<svg>{TREE} dark</svg>",
        "v1",
    )


def test_a_re_seed_draws_nothing_the_same_tool_drew(database, tmp_path):
    """A draw costs about a second, and a module holds about 160 sources."""
    source = read_module(module(tmp_path))
    seed_module(source, root=database, drawer=Fake())
    again = Fake()

    result = seed_module(source, root=database, drawer=again)

    assert (result.diagrams, again.drawn) == (0, [])


def test_a_new_version_of_the_tool_draws_every_source_again(database, tmp_path):
    """A fix to how the SVG is prepared reaches the drawings already stored."""
    source = read_module(module(tmp_path))
    seed_module(source, root=database, drawer=Fake("v1"))
    newer = Fake("v2")

    result = seed_module(source, root=database, drawer=newer)

    assert result.diagrams == 2
    assert {row["tool"] for row in rows(database, diagrams)} == {"v2"}


def test_a_failed_draw_refuses_the_module_and_writes_nothing(database, tmp_path):
    """A lesson seeded without its drawing would show its source as text."""
    result = seed_module(read_module(module(tmp_path)), root=database, drawer=Fake(fail="bad"))

    assert result.refused == ["diagrams: bad"]
    assert rows(database, modules) == []


def test_a_module_without_mermaid_never_runs_the_tool(database, tmp_path):
    """A module drawn in text alone seeds where the tool is not installed."""
    plain = authored(tmp_path)

    result = seed_module(read_module(plain), root=database, drawer=Fake(fail="not installed"))

    assert (result.refused, result.diagrams) == ([], 0)


def test_the_tool_names_its_install_where_it_is_missing(tmp_path, monkeypatch):
    """The seed then refuses with the command that fixes it."""
    monkeypatch.setattr(drawing, "TOOL", tmp_path)

    with pytest.raises(DrawError, match="just diagrams-install"):
        MermaidCli().version()
