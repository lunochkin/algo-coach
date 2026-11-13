"""Rules 27 and 28, and rule 19 for a module written by concept:
docs/authoring/concepts.md."""

import re
from collections import defaultdict

from algo_coach.knowledge.authoring.course import Course, Report, where
from algo_coach.knowledge.authoring.static import anchor

REQUIRED = ("id", "level", "claim", "source", "misconceptions", "taught_by")
HEADING = re.compile(r"^## (.+)$", re.M)
# the seed renders these from the concepts, so a file holding one holds a copy
RENDERED = ("common-mistakes", "go-deeper")


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
        if "#" not in concept.get("source", "#"):
            report.error(27, at, "the source names no section")
        if concept.get("level") not in (0, 1, 2, 3):
            report.error(27, at, f"level {concept.get('level')!r}")
        if not concept.get("misconceptions"):
            report.error(27, at, "no misconception")


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
    question. A question is filed by its `concept`, which rule 27 resolves."""
    asked = {q.get("concept") for q in course.questions}
    for name, concept in course.concepts.items():
        if name not in asked:
            report.warn(19, f"{concept['_file']} {name}", "no question tests this concept")
    for q in course.questions:
        if "concept" not in q:
            report.error(19, where(q), "names no concept")


def _heads(text: str) -> set[str]:
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    return {anchor(h) for h in HEADING.findall(prose)}
