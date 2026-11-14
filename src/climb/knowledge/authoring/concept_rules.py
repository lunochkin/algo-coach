"""Rules 27 and 28, and rules 15 and 19 for a module written by concept:
docs/authoring/concepts.md."""

import builtins
import keyword
import re
from collections import defaultdict
from typing import Any, cast

from climb.knowledge.authoring.course import Course, Report, where
from climb.knowledge.authoring.static import anchor
from climb.knowledge.concepts import owner, sources

REQUIRED = ("id", "level", "claim", "source", "misconceptions", "taught_by")
HEADING = re.compile(r"^## (.+)$", re.M)
# the seed renders these from the concepts, so a file holding one holds a copy
RENDERED = ("common-mistakes", "go-deeper")
CODE = re.compile(r"```\w*\n(.*?)```|`([^`\n]+)`", re.S)
# a literal or a name; an attribute and a keyword argument name the API taught
TOKEN = re.compile(r"(?<![\w.])(?:'[^'\n]+'|\"[^\"\n]+\"|[A-Za-z_]\w*(?!\w|=[^=])|\d+(?:\.\d+)?)")
COMMON = frozenset([*keyword.kwlist, *keyword.softkwlist, *dir(builtins), "self"])


def records(course: Course, report: Report) -> None:
    """Rule 27: a concept holds every field, and a witness with its output or a
    quote; the reading found no unknown concept and no restated field."""
    for line in course.unread:
        where_, _, text = line.partition(": ")
        report.error(27, where_, text)
    for name, concept in course.concepts.items():
        at = f"{concept['_file']} {name}"
        if missing := [f for f in REQUIRED if f not in concept]:
            report.error(27, at, f"missing {missing}")
        if "witness" in concept and "output" not in concept:
            report.error(27, at, "a witness with no output")
        if "witness" not in concept and "quote" not in concept:
            report.error(27, at, "neither a witness nor a quote")
        if any("#" not in url for url in sources(concept)):
            report.error(27, at, "a source names no section")
        if concept.get("level") not in (0, 1, 2, 3):
            report.error(27, at, f"level {concept.get('level')!r}")
        _misconceptions(report, at, concept)


def taught(course: Course, report: Report) -> None:
    """Rule 28: each `taught_by` names a section, each section of a lesson
    teaching concepts is named, and the file holds no intro and no section the
    seed renders."""
    named: dict[str, set[str]] = defaultdict(set)
    for name, concept in course.concepts.items():
        slug, _, at = concept.get("taught_by", "").partition("#")
        named[slug].add(at)
        heads = _heads(course.lessons.get(slug, ""))
        if slug not in course.lessons or at not in heads:
            report.error(
                28, f"{concept['_file']} {name}", f"taught_by {slug}#{at} names no section"
            )
    for slug in named.keys() & course.lessons.keys():
        text = course.lessons[slug]
        file = f"lessons/{slug}.md"
        if text.strip() and not text.lstrip().startswith("## "):
            report.error(28, file, "holds an intro, which the seed renders from the headings")
        for head in _heads(text):
            if head in RENDERED:
                report.error(28, file, f"holds #{head}, which the seed renders from the concepts")
            elif head not in named[slug]:
                report.error(28, file, f"#{head} teaches no concept")


def filed(course: Course, report: Report) -> None:
    """Rule 19 where the concepts replace the coverage map: every concept has a
    question, and every misconception a wrong choice embodying it. A question
    is filed by its `concept`, which rule 27 resolves."""
    asked = {q.get("concept") for q in course.questions}
    targeted = {
        owner(ref, q.get("concept", "")) for q in course.questions for ref in _targets(q).values()
    }
    for name, concept in course.concepts.items():
        at = f"{concept['_file']} {name}"
        if name not in asked:
            report.warn(19, at, "no question tests this concept")
            continue
        for wrong in concept.get("misconceptions", []):
            if (name, wrong.get("id")) not in targeted:
                report.warn(19, at, f"no wrong choice embodies misconception {wrong.get('id')}")
    for q in course.questions:
        if "concept" not in q:
            report.error(19, where(q), "names no concept")
        elif q.get("format", "choice") == "choice":
            wrong = {chr(65 + i) for i in range(len(q["choices"]))} - set(q["answer"])
            if bare := sorted(wrong - _targets(q).keys()):
                report.warn(19, where(q), f"wrong choice {', '.join(bare)} names no misconception")
            if keyed := sorted(_targets(q).keys() & set(q["answer"])):
                report.error(19, where(q), f"keyed choice {', '.join(keyed)} names a misconception")


def shared(course: Course, report: Report) -> None:
    """Rule 15: a question shares no name or literal with its section's code.
    Catches a renamed copy keeping a value, never a copy of shape alone."""
    skipped = course.skip.get("lesson-repeat", {})
    for q in course.questions:
        concept = course.concepts.get(q.get("concept", ""))
        if concept is None or q["id"] in skipped:
            continue
        slug, _, at = concept["taught_by"].partition("#")
        own = q.get("code", "") + _code(
            q["prompt"] + " ".join(q.get("key", []) + q.get("traps", []))
        )
        common = _tokens(own) & _tokens(_code(_section(course.lessons.get(slug, ""), at)))
        if found := sorted(common - _tokens(_code(concept["claim"]))):
            report.warn(15, where(q), f"shares {', '.join(found[:6])} with {slug}#{at}")


def _code(text: str) -> str:
    return "\n".join(m[1] or m[2] for m in CODE.finditer(text))


def _tokens(code: str) -> set[str]:
    return {
        t
        for t in TOKEN.findall(code)
        if t not in COMMON
        and not t.startswith("__")
        and not re.fullmatch(r"[A-Za-z_]|\d|['\"][\W_]*['\"]", t)
    }


def _section(text: str, at: str) -> str:
    for part in re.split(r"^## ", text, flags=re.M)[1:]:
        if anchor(part.splitlines()[0]) == at:
            return part
    return ""


def _targets(q: dict[str, Any]) -> dict[str, str]:
    found = q.get("misconception", {})
    return cast(dict[str, str], found) if isinstance(found, dict) else {}


def _misconceptions(report: Report, at: str, concept: dict[str, Any]) -> None:
    found = concept.get("misconceptions")
    if not isinstance(found, list) or not found:
        report.error(27, at, "no misconception")
        return
    ids: list[str] = []
    for wrong in cast(list[object], found):
        if not isinstance(wrong, dict) or {"id", "text"} - cast(dict[str, Any], wrong).keys():
            report.error(27, at, "a misconception is not { id, text }")
            continue
        ids.append(str(cast(dict[str, Any], wrong)["id"]))
    if len(ids) != len(set(ids)):
        report.error(27, at, "two misconceptions share an id")


def _heads(text: str) -> set[str]:
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    return {anchor(h) for h in HEADING.findall(prose)}
