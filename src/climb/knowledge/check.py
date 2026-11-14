"""learn's `learn check` over questions and lessons, ported as it was worded.
The graph and the certification settings are stored as authored: a client
ignores a graph that fails its own check, as `knowledge.md` gives."""

import re
from collections.abc import Mapping
from typing import Any, cast

from pydantic import ValidationError

from climb.knowledge.files import ModuleSource
from climb.schema import BODIES, CertificationSettings, GraphSettings, QuestionFormat
from climb.schema.authored import LEVEL_NAMES, LEVELS

FORMATS = ("choice", "short", "card")
# held in a column of its own, so never part of the body
COLUMNS = {"id", "kind", "level", "prompt", "lesson", "code", "format", "sub"}
COMMON = {"id", "kind", "prompt", "level"}
REQUIRED = {
    "choice": COMMON | {"choices", "answer", "explain", "why", "detail"},
    "short": COMMON | {"accept", "explain", "detail"},
    "card": COMMON | {"key"},
}
HEADING = re.compile(r"#{2,3}\s+(.+?)\s*#*\s*$")


def refusals(source: ModuleSource) -> list[str]:
    found = list(source.unread) + _settings(source) + _sub_titles(source)
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
    if raw["level"] not in LEVELS:
        found.append(f"bad level {raw['level']!r}")
    if raw["kind"] in code_kinds and not raw.get("code"):
        found.append(f"{raw['kind']} without code")
    body = {key: value for key, value in raw.items() if key not in COLUMNS}
    try:
        BODIES[QuestionFormat.OPEN if form == "card" else QuestionFormat(form)].model_validate(body)
    except ValidationError as error:
        found += [_message(one) for one in error.errors()]
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


def _message(error: Mapping[str, Any]) -> str:
    where = ".".join(str(part) for part in error["loc"])
    text = error["msg"].removeprefix("Value error, ")
    return f"{where}: {text}" if where else text


def _settings(source: ModuleSource) -> list[str]:
    """The graph and the certification settings, typed, and every slug and id
    they name resolved, as `learn check` did."""
    topics = source.course.get("topic", [])
    subs = {sub for topic in topics for sub in topic.get("subs", [])}
    found: list[str] = []
    graph: GraphSettings | None = None
    authored = {k: v for k, v in (source.graph or {}).items() if k not in ("lesson", "exercise")}
    try:
        graph = GraphSettings.model_validate(authored)
    except ValidationError as error:
        found += [f"graph: {_message(one)}" for one in error.errors()]
    if graph is not None:
        for needs, to, offset in graph.edges():
            found += [f"unknown subtopic {one!r}" for one in (needs, to) if one not in subs]
            if needs == to:
                found.append(f"{needs} needs itself")
            if min(max(LEVELS), graph.match_up_to) + offset > max(LEVELS):
                found.append(f"{needs} -> {to}: offset {offset} needs a level above {max(LEVELS)}")
        if cycle := _cycle(graph.edges()):
            found.append(f"cycle: {' -> '.join(cycle)}")
    if source.certifications is None:
        return found
    try:
        settings = CertificationSettings.model_validate(source.certifications)
    except ValidationError as error:
        return found + [f"certs: {_message(one)}" for one in error.errors()]
    scopes = [topic["slug"] for topic in topics] + ["all"]
    found += [f"unknown scope {one!r}" for one in settings.scope if one not in scopes]
    ids = {f"{source.slug}-{scope}-{level}" for scope in scopes for level in LEVEL_NAMES}
    for name, edges in (("edge", settings.edge), ("unedge", settings.unedge)):
        for edge in edges:
            found += [
                f"{name}: unknown certificate {one!r}"
                for one in (edge.needs, edge.to)
                if one not in ids
            ]
    return found


def _cycle(edges: list[tuple[str, str, int]]) -> list[str] | None:
    """A subtopic needing itself through others, as the path that closes it."""
    needs: dict[str, list[str]] = {}
    for one, to, _ in edges:
        needs.setdefault(one, []).append(to)
    state: dict[str, int] = {}  # 1 visiting, 2 done

    def visit(node: str, path: list[str]) -> list[str] | None:
        state[node] = 1
        for to in needs.get(node, []):
            if state.get(to) == 1:
                return [*path[path.index(to) :], to] if to in path else [node, to]
            if state.get(to) is None and (closed := visit(to, [*path, to])):
                return closed
        state[node] = 2
        return None

    for node in needs:
        if state.get(node) is None and (closed := visit(node, [node])):
            return closed
    return None


def _sub_titles(source: ModuleSource) -> list[str]:
    """A topic's `sub_titles`: a title per subtopic the topic lists, and nothing
    else."""
    found: list[str] = []
    for topic in source.course.get("topic", []):
        named = f"topic {topic.get('slug')}"
        titles = topic.get("sub_titles", {})
        if not isinstance(titles, dict):
            found.append(f"{named}: sub_titles must be a table")
            continue
        for slug, title in cast(dict[str, object], titles).items():
            if slug not in topic.get("subs", []):
                found.append(f"{named}: sub_titles names {slug!r}, which subs does not list")
            if not (isinstance(title, str) and title.strip()):
                found.append(f"{named}: the title of {slug!r} must be non-empty text")
    return found
