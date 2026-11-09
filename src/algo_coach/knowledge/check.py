"""learn's `learn check` over questions and lessons, ported as it was worded.
The graph and the certification settings are stored as authored: a client
ignores a graph that fails its own check, as `knowledge.md` gives."""

import re
from typing import Any, cast

from algo_coach.knowledge.files import ModuleSource

LETTERS = "ABCDEFGH"
RANKS = (0, 1, 2, 3)
FORMATS = ("choice", "short", "card")
DETAIL_FIELDS = ("mechanism", "example", "pitfalls", "versions", "diagram")
COMMON = {"id", "kind", "prompt", "level"}
REQUIRED = {
    "choice": COMMON | {"choices", "answer", "explain", "why", "detail"},
    "short": COMMON | {"accept", "explain", "detail"},
    "card": COMMON | {"key"},
}
HEADING = re.compile(r"#{2,3}\s+(.+?)\s*#*\s*$")


def refusals(source: ModuleSource) -> list[str]:
    found = list(source.unread)
    course = source.course
    kinds, code_kinds = course.get("kinds", []), course.get("code_kinds", [])
    with_lessons = bool((source.graph or {}).get("lesson"))
    seen: dict[str, str] = {}
    for bank in source.banks:
        where = f"{bank.topic}/{bank.sub}"
        for raw in bank.questions:
            at = f"{where}:{raw.get('id', '?')}"
            found += [f"{at}: {one}" for one in _question(raw, seen, where, kinds, code_kinds)]
            if ref := raw.get("lesson"):
                if not isinstance(ref, str):
                    found.append(f"{at}: lesson must be a string")
                elif error := _lesson_ref(ref, source.lesson_texts):
                    found.append(f"{at}: lesson: {error}")
            elif with_lessons:
                found.append(f"{at}: no lesson (every question names its lesson section)")
    return found


def _question(
    raw: dict[str, Any], seen: dict[str, str], where: str, kinds: list[str], code_kinds: list[str]
) -> list[str]:
    form = raw.get("format", "choice")
    if form not in FORMATS:
        return [f"bad format {form!r}"]
    if missing := REQUIRED[form] - raw.keys():
        return [f"missing {sorted(missing)}"]
    found: list[str] = []
    if raw["id"] in seen:
        found.append(f"duplicate id (also in {seen[raw['id']]})")
    seen[raw["id"]] = where
    if raw["kind"] not in kinds:
        found.append(f"kind {raw['kind']!r} not in course kinds")
    if raw["level"] not in RANKS:
        found.append(f"bad level {raw['level']!r}")
    if raw["kind"] in code_kinds and not raw.get("code"):
        found.append(f"{raw['kind']} without code")
    if form == "short" and not raw["accept"]:
        found.append("empty accept")
    if form == "card":
        found += _card(raw)
    found += _detail(raw)
    if form == "choice":
        found += _choices(raw)
    return found


def _choices(raw: dict[str, Any]) -> list[str]:
    found: list[str] = []
    n = len(raw["choices"])
    if not 3 <= n <= len(LETTERS):
        found.append(f"{n} choices")
    if len(raw["why"]) != n:
        found.append(f"{len(raw['why'])} why for {n} choices")
    answer = raw["answer"]
    if not answer or len(set(answer)) != len(answer) or any(a not in LETTERS[:n] for a in answer):
        found.append(f"bad answer {answer!r}")
    return found


def _card(raw: dict[str, Any]) -> list[str]:
    found: list[str] = []
    if not _strings(raw["key"], 2, 6):
        found.append("key must be a list of 2-6 non-empty points")
    if "traps" in raw and not _strings(raw["traps"], 0, 3):
        found.append("traps must be a list of 0-3 non-empty strings")
    return found


def _detail(raw: dict[str, Any]) -> list[str]:
    found: list[str] = []
    detail: object = raw.get("detail")
    if isinstance(detail, str):
        found.append("detail must be a table with mechanism (a plain string is legacy)")
    elif isinstance(detail, dict):
        detail = cast(dict[str, Any], detail)
        if not (isinstance(detail.get("mechanism"), str) and detail["mechanism"].strip()):
            found.append("detail.mechanism is required")
        for name in ("example", "versions", "diagram"):
            if name in detail and not (isinstance(detail[name], str) and detail[name].strip()):
                found.append(f"detail.{name} must be a non-empty string")
        if "pitfalls" in detail and not _strings(detail["pitfalls"], 1, 4):
            found.append("detail.pitfalls must be 1-4 non-empty strings")
        if extra := sorted(set(detail) - set(DETAIL_FIELDS)):
            found.append(f"detail has unknown fields {extra}")
    elif detail is not None:
        found.append("detail must be a table")
    return found + _paired(raw)


def _paired(raw: dict[str, Any]) -> list[str]:
    """`key_detail` and `traps_detail`, one string per point or trap."""
    found: list[str] = []
    for name, parent in (("key_detail", "key"), ("traps_detail", "traps")):
        if name not in raw:
            continue
        value, n = raw[name], len(raw.get(parent) or [])
        if not _strings(value, n, n):
            found.append(f"{name} must have one non-empty string per {parent} item ({n})")
        elif any(len(one.strip().splitlines()) > 3 for one in value):
            found.append(f"{name} items must be at most 3 lines")
    return found


def _lesson_ref(ref: str, texts: dict[str, str]) -> str | None:
    slug, _, anchor = ref.partition("#")
    if slug not in texts:
        return f"unknown lesson {slug!r}"
    if anchor and anchor not in _anchors(texts[slug]):
        return f"no section #{anchor} in lesson {slug}"
    return None


def _anchors(markdown: str) -> set[str]:
    """GitHub-style anchors of the `##` and `###` headings outside fences."""
    found: set[str] = set()
    fenced = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        elif not fenced and (match := HEADING.match(line)):
            found.add(re.sub(r"[^\w\- ]", "", match[1].strip().lower()).replace(" ", "-"))
    return found


def _strings(value: object, lo: int, hi: int) -> bool:
    if not isinstance(value, list):
        return False
    items = cast(list[object], value)
    return lo <= len(items) <= hi and all(isinstance(one, str) and one.strip() for one in items)
