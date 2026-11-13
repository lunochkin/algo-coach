"""A module written by concept: docs/authoring/concepts.md."""

import re
import tomllib
from pathlib import Path
from typing import Any

DERIVED = ("lesson", "level", "detail")
HEADING = re.compile(r"^##\s+(.+?)\s*$", re.M)


def read_concepts(base: Path, unread: list[str]) -> dict[str, dict[str, Any]]:
    concepts: dict[str, dict[str, Any]] = {}
    for path in sorted((base / "concepts").glob("*/*.toml")):
        try:
            raws = tomllib.loads(path.read_text()).get("concept", [])
        except tomllib.TOMLDecodeError as error:
            unread.append(f"concepts/{path.parent.name}/{path.name}: {error}")
            continue
        for concept in raws:
            concept["_file"] = f"concepts/{path.parent.name}/{path.name}"
            if concept["id"] in concepts:
                unread.append(f"concept {concept['id']}: duplicate id")
            concepts[concept["id"]] = concept
    return concepts


def derive(where: str, raw: dict[str, Any], concepts: dict[str, dict[str, Any]]) -> list[str]:
    """Fill a question's derived fields from its concept, in place."""
    name = raw.get("concept")
    if name is None:
        return []
    at = f"{where}:{raw.get('id', '?')}"
    if name not in concepts:
        return [f"{at}: unknown concept {name}"]
    if restated := [field for field in DERIVED if field in raw]:
        return [f"{at}: {field} is derived from concept {name}" for field in restated]
    concept = concepts[name]
    ids = {m["id"] for m in concept["misconceptions"]}
    # a choice's letter to the misconception it embodies, by its stable id
    targeted = raw.get("misconception", {})
    if unknown := sorted(set(targeted.values()) - ids):
        return [f"{at}: no misconception {i} in concept {name}" for i in unknown]
    raw["lesson"] = concept["taught_by"]
    raw["level"] = concept["level"]
    raw["detail"] = {"mechanism": concept["claim"], "pitfalls": texts(concept)}
    return []


def texts(concept: dict[str, Any]) -> list[str]:
    return [m["text"] for m in concept["misconceptions"]]


def rendered(slug: str, text: str, concepts: dict[str, dict[str, Any]]) -> str:
    """The lesson as served: an intro from its headings, then the authored
    sections, then the mistakes and links of the concepts it teaches."""
    taught = [c for c in concepts.values() if c["taught_by"].split("#")[0] == slug]
    if not taught:
        return text
    intro = f"This lesson covers {_listed(HEADING.findall(text))}."
    mistakes = "".join(f"- Wrong: {m}\n" for c in taught for m in texts(c))
    sources = dict.fromkeys(c["source"] for c in taught)
    links = "".join(f"- [{_label(url)}]({url})\n" for url in sources)
    return (
        f"{intro}\n\n{text.rstrip()}\n\n## Common mistakes\n\n{mistakes}\n## Go deeper\n\n{links}"
    )


def _listed(items: list[str]) -> str:
    lowered = [item[0].lower() + item[1:] if item[:1].isupper() else item for item in items]
    if len(lowered) < 2:
        return "".join(lowered)
    return ", ".join(lowered[:-1]) + " and " + lowered[-1]


def _label(url: str) -> str:
    # "#the-while-statement" reads "The while statement"
    page, _, anchor = url.partition("#")
    words = anchor or page.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html")
    return words.replace("-", " ").capitalize()
