import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHITECTURE = sorted((ROOT / "docs" / "architecture").glob("*.md"))
SRC = ROOT / "src" / "algo_coach"

# `CLAUDE.md`, Writing: one idea per sentence, nothing over forty words, split
# at the em-dash and the semicolon. The docs predate the rule, so each count
# is held where it stands and lowered as they are edited, never raised.
LONG_SENTENCES = 3
EM_DASHES = 26
SEMICOLONS = 25
# `CLAUDE.md`, Writing: no cleft sentences, and no sentence opening on an
# abstraction that delays its subject. Held and lowered the same way.
CLEFTS = 77
FRONTED = 67
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
