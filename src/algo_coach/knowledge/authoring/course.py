"""A module's authored files, read as the module check reads them, and the
report its rules fill."""

import re
import tomllib
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# a question as its bank holds it, plus `_sub` and `_file`
type Question = dict[str, Any]


@dataclass
class Report:
    errors: list[str] = field(default_factory=list[str])
    warnings: list[str] = field(default_factory=list[str])
    missing: dict[str, int] = field(default_factory=lambda: defaultdict[str, int](int))
    made_up: int = 0
    fragments: int = 0
    unreplayed: list[str] = field(default_factory=list[str])

    def error(self, rule: int, where: str, text: str) -> None:
        self.errors.append(f"[{rule}] {where}: {text}")

    def warn(self, rule: int, where: str, text: str) -> None:
        self.warnings.append(f"[{rule}] {where}: {text}")


@dataclass
class Course:
    root: Path
    questions: list[Question]
    graph: dict[str, Any]
    lessons: dict[str, str]
    coverage: dict[str, dict[str, Any]]
    skip: dict[str, dict[str, str]]
    versions: list[str]
    builds: list[str]
    expect: dict[str, dict[str, str]]
    settings: dict[str, Any]
    # made-up modules a snippet imports to stand for the reader's own code
    fixtures: set[str]


def load(root: Path) -> Course:
    questions: list[Question] = []
    for path in sorted((root / "banks").rglob("*.toml")):
        for q in tomllib.loads(path.read_text()).get("q", []):
            q["_sub"] = path.stem
            q["_file"] = str(path.relative_to(root))
            questions.append(q)
    graph = tomllib.loads((root / "graph.toml").read_text())
    lessons = {
        slug: (root / one["file"]).read_text() for slug, one in graph.get("lesson", {}).items()
    }
    coverage = {
        p.stem: tomllib.loads(p.read_text()) for p in sorted((root / "coverage").glob("*.toml"))
    }
    skip_file = root / "check.toml"
    config = tomllib.loads(skip_file.read_text()) if skip_file.exists() else {}
    return Course(
        root=root,
        questions=questions,
        graph=graph,
        lessons=lessons,
        coverage=coverage,
        skip=config.get("skip", {}),
        versions=config.get("versions", []),
        builds=config.get("builds", []),
        expect=config.get("expect", {}),
        settings=tomllib.loads((root / "course.toml").read_text()),
        fixtures=set(config.get("fixtures", [])),
    )


def fmt(q: Question) -> str:
    return q.get("format", "choice")


def where(q: Question) -> str:
    return f"{q['_file']} {q['id']}"


def norm(text: str) -> str:
    text = re.sub(r"0x[0-9a-f]+", "0x...", text)
    return re.sub(r"[\s'\"`]", "", text).lower()
