"""A knowledge module written to disk for the module check, committed to a git
repository of its own, since rule 21 reads the banks' history."""

import json
import subprocess
from pathlib import Path

LESSON = "# Lesson\n\n## Section\n\nProse.\n"


def question(qid: str, **fields) -> dict:
    """A concept choice question pointing at the default lesson's section."""
    return {
        "id": qid,
        "kind": "concept",
        "level": 0,
        "prompt": f"What does {qid} ask?",
        "lesson": "les#section",
        "choices": ["one", "two", "three"],
        "answer": ["A"],
        "explain": f"Explained for {qid}.",
        "why": ["a", "b", "c"],
        "detail": {"mechanism": f"How {qid} works."},
    } | fields


def _value(value) -> str:
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{k} = {_value(v)}" for k, v in value.items()) + " }"
    return json.dumps(value)


def _bank(questions: list[dict]) -> str:
    blocks = []
    for q in questions:
        blocks.append("[[q]]\n" + "".join(f"{k} = {_value(v)}\n" for k, v in q.items()))
    return "\n".join(blocks)


def _coverage(questions: list[dict]) -> str:
    """One concept per question, at its level, so rule 19 holds."""
    text = "[subtopic.sub]\n"
    for q in questions:
        text += (
            f"[[subtopic.sub.concept]]\nid = {json.dumps(q['id'])}\n"
            f"level = {q['level']}\ncovered_by = [{json.dumps(q['id'])}]\n"
        )
    return text


def git(root: Path, *argv: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *argv],
        cwd=root,
        check=True,
        capture_output=True,
    )


def written(
    where: Path,
    questions: list[dict],
    *,
    lessons: dict[str, tuple[list[str], str]] | None = None,
    coverage: str | None = None,
    check: str = "",
) -> Path:
    """The module's directory. A lesson is its `teaches` list and its text."""
    root = where / "modules" / "m"
    lessons = {"les": (["sub@0"], LESSON)} if lessons is None else lessons
    (root / "banks" / "t").mkdir(parents=True)
    (root / "lessons").mkdir()
    (root / "coverage").mkdir()
    (root / "course.toml").write_text(
        'title = "M"\npass_ratio = 0.8\nkinds = ["concept", "output", "debug"]\n'
        'code_kinds = ["output", "debug"]\n'
    )
    graph = ""
    for slug, (teaches, text) in lessons.items():
        graph += f'[lesson.{slug}]\nfile = "lessons/{slug}.md"\nteaches = {json.dumps(teaches)}\n'
        (root / "lessons" / f"{slug}.md").write_text(text)
    (root / "graph.toml").write_text(graph)
    (root / "banks" / "t" / "sub.toml").write_text(_bank(questions))
    (root / "coverage" / "t.toml").write_text(
        _coverage(questions) if coverage is None else coverage
    )
    if check:
        (root / "check.toml").write_text(check)
    if not (where / ".git").exists():
        git(where, "init", "-q")
    git(where, "add", "-A")
    git(where, "commit", "-q", "--allow-empty", "-m", "module")
    return root


def rebanked(root: Path, questions: list[dict]) -> None:
    """The bank rewritten and committed, as a later edit is."""
    (root / "banks" / "t" / "sub.toml").write_text(_bank(questions))
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "edit")


def found(lines: list[str], rule: int) -> list[str]:
    return [line for line in lines if line.startswith(f"[{rule}] ")]
