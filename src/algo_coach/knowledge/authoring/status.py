"""Which subtopics a module written by concept holds at each level, read from
its course, concept and bank files."""

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LEVELS = range(4)


@dataclass(frozen=True)
class Written:
    concepts: int
    questions: int


@dataclass(frozen=True)
class Subtopic:
    topic: str
    slug: str
    levels: dict[int, Written]


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    subtopics: list[Subtopic]

    def done(self, level: int) -> int:
        return sum(1 for s in self.subtopics if level in s.levels)


def topics(root: Path) -> list[Topic]:
    course = tomllib.loads((root / "course.toml").read_text())
    return [
        Topic(
            t["slug"],
            t.get("title", t["slug"]),
            [Subtopic(t["slug"], s, written(root, t["slug"], s)) for s in t.get("subs", [])],
        )
        for t in course.get("topic", [])
    ]


def written(root: Path, topic: str, slug: str) -> dict[int, Written]:
    """A level is written when the concept file holds a concept at it."""
    path = root / "concepts" / topic / f"{slug}.toml"
    if not path.exists():
        return {}
    concepts = tomllib.loads(path.read_text()).get("concept", [])
    level = {c["id"]: c["level"] for c in concepts}
    bank = root / "banks" / topic / f"{slug}.toml"
    questions: list[dict[str, Any]] = (
        tomllib.loads(bank.read_text()).get("q", []) if bank.exists() else []
    )
    return {
        n: Written(
            sum(1 for c in concepts if c["level"] == n),
            sum(1 for q in questions if level.get(q.get("concept")) == n),
        )
        for n in sorted(set(level.values()))
    }


def markdown(module: str, found: list[Topic]) -> str:
    head = [
        f"# `{module}` status",
        "",
        f"Written by `algo-coach module status {module}`, never by hand. A subtopic is",
        "written at a level when its concept file holds a concept at that level. A",
        "cell gives the concepts, then the questions.",
    ]
    body: list[str] = []
    for topic in found:
        tally = ", ".join(f"L{n} {topic.done(n)} of {len(topic.subtopics)}" for n in LEVELS)
        body += ["", f"## {topic.slug}: {topic.title}", "", tally, ""]
        body += ["| Subtopic | L0 | L1 | L2 | L3 |", "|---|---|---|---|---|"]
        for sub in topic.subtopics:
            cells = [
                f"{w.concepts} / {w.questions}" if (w := sub.levels.get(n)) else "—" for n in LEVELS
            ]
            body.append(f"| {sub.slug} | " + " | ".join(cells) + " |")
    return "\n".join(head + body) + "\n"
