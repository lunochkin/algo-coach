import ast
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE = sorted((ROOT / "docs" / "architecture").glob("*.md"))
SRC = ROOT / "src" / "algo_coach"
DOCS = [*sorted((ROOT / "docs").rglob("*.md")), ROOT / "README.md", ROOT / "CLAUDE.md"]
PROSE_WIDTH = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["ruff"]["lint"][
    "pycodestyle"
]["max-doc-length"]

# `CLAUDE.md`, Writing: one idea per sentence, nothing over forty words, split
# at the em-dash and the semicolon. Each count is a ratchet: held at zero, and
# never raised.
LONG_SENTENCES = 0
EM_DASHES = 0
SEMICOLONS = 0
# `CLAUDE.md`, Writing: no cleft sentences, and no sentence opening on an
# abstraction that delays its subject. Held at zero the same way.
CLEFTS = 0
FRONTED = 0
# `CLAUDE.md`, Code style: a docstring stays shorter than the code it sits on.
LONGER_DOCSTRINGS = 36


def prose(path: Path) -> str:
    text = re.sub(r"```.*?```", "", path.read_text(), flags=re.S)
    return re.sub(r"^\|.*$", "", text, flags=re.M)


def sentences(text: str) -> list[str]:
    # a bold headline ends in `.**`, and the sentence after it is its own
    return re.split(r"(?<=[.!?])(?:\*\*)?\s+", re.sub(r"\s+", " ", text))


CLEFT = re.compile(r"\b(?:is|are|was|were) (?:what|where|why|how)\b")
OPENERS = ("What", "Where", "Neither", "Both", "Nothing")


def opener(sentence: str) -> str:
    """The first word, past a list marker and any emphasis."""
    words = re.sub(r"^(?:[-*]|\d+\.)?\s*[*`_]*", "", sentence).split()
    return words[0].rstrip(",:") if words else ""


def test_no_sentence_in_the_architecture_runs_past_forty_words():
    over = [
        f"{path.name}: {one[:60]}..."
        for path in ARCHITECTURE
        for one in sentences(prose(path))
        if len(one.split()) > 40
    ]
    assert len(over) <= LONG_SENTENCES, over


def test_the_architecture_states_the_subject_rather_than_clefting_it():
    """ "The reference is what discards" names the subject after the verb, and
    a reader holds the verb until it arrives."""
    clefts = [
        f"{path.name}: {one[:60]}..."
        for path in ARCHITECTURE
        for one in sentences(prose(path))
        if CLEFT.search(one)
    ]
    assert len(clefts) <= CLEFTS, clefts


def test_no_sentence_in_the_architecture_opens_on_an_abstraction():
    """`What`, `Where`, `Neither`, `Both` and `Nothing` front an abstraction and
    hold the concrete noun back to the end of the sentence."""
    fronted = [
        f"{path.name}: {one[:60]}..."
        for path in ARCHITECTURE
        for one in sentences(prose(path))
        if opener(one) in OPENERS
    ]
    assert len(fronted) <= FRONTED, fronted


def test_the_architecture_splits_where_it_would_chain():
    dashes = sum(prose(path).count("—") for path in ARCHITECTURE)
    semicolons = sum(prose(path).count(";") for path in ARCHITECTURE)
    assert dashes <= EM_DASHES
    assert semicolons <= SEMICOLONS


def test_a_docstring_is_shorter_than_the_code_it_sits_on():
    """Over that, the reason belongs in `docs/architecture/` and the code cites
    it. Tests are the exception, and are not counted."""
    longer = []
    for path in sorted(SRC.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if ast.get_docstring(node) is None or len(node.body) < 2:
                continue
            docstring, first = node.body[0], node.body[1]
            assert docstring.end_lineno and node.end_lineno
            doc = docstring.end_lineno - docstring.lineno + 1
            code = node.end_lineno - first.lineno + 1
            if doc > code:
                longer.append(f"{path.relative_to(ROOT)}:{node.name} ({doc} over {code})")
    assert len(longer) <= LONGER_DOCSTRINGS, longer


def test_no_prose_line_in_the_docs_is_wider_than_a_comment():
    """One prose width, set in `pyproject.toml`, which ruff reads for comments
    and docstrings. A table, a fenced block and a line holding no space cannot
    be wrapped, so none of them counts."""
    wide = []
    for path in DOCS:
        fenced = False
        for number, line in enumerate(path.read_text().splitlines(), 1):
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if fenced or line.lstrip().startswith("|") or " " not in line.strip():
                continue
            if len(line) > PROSE_WIDTH:
                wide.append(f"{path.relative_to(ROOT)}:{number}")
    assert wide == []
