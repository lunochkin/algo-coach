"""Rule 29: the writing rules a program can check, over a module written by
concept: its claims, its misconceptions and its lesson prose."""

import re

from algo_coach.knowledge.authoring.course import Course, Report

OPENERS = ("What", "Where", "Neither", "Both", "Nothing")
LONGEST = 40
# Oxford spelling takes -ize; these are spelt -ise in every English
ISE = frozenset(
    {
        "advise",
        "arise",
        "chastise",
        "clockwise",
        "comprise",
        "compromise",
        "concise",
        "despise",
        "devise",
        "disguise",
        "enterprise",
        "excise",
        "exercise",
        "expertise",
        "franchise",
        "improvise",
        "incise",
        "likewise",
        "merchandise",
        "noise",
        "otherwise",
        "paradise",
        "poise",
        "praise",
        "precise",
        "premise",
        "promise",
        "raise",
        "revise",
        "rise",
        "rising",
        "supervise",
        "surprise",
        "televise",
        "wise",
    }
)
ISED = re.compile(r"\b([a-z]+)is(e|es|ed|ing|ation|ations)\b", re.I)
AMERICAN = re.compile(r"\b(color\w*|behavior\w*|center(?:s|ed|ing)?|analyz\w+|catalog)\b", re.I)
CODE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"```.*?```", re.S)


def prose(course: Course, report: Report) -> None:
    for name, concept in course.concepts.items():
        at = f"{concept['_file']} {name}"
        _lint(report, at, concept.get("claim", ""))
        for wrong in concept.get("misconceptions", []):
            _lint(report, at, wrong)
    taught = {c.get("taught_by", "").partition("#")[0] for c in course.concepts.values()}
    for slug in taught & course.lessons.keys():
        for para in FENCE.sub("", course.lessons[slug]).split("\n\n"):
            if not para.lstrip().startswith("#"):
                _lint(report, f"lessons/{slug}.md", para.replace("\n", " "))


def _lint(report: Report, at: str, text: str) -> None:
    plain = CODE.sub("CODE", text)
    for sentence in re.split(r"(?<=[.!?])\s+", plain.strip()):
        first = sentence.lstrip("-* ").split(" ", 1)[0]
        if first in OPENERS:
            report.warn(29, at, f"a sentence opens with {first!r}: {sentence[:50]!r}")
        if len(sentence.split()) > LONGEST:
            report.warn(29, at, f"a sentence of {len(sentence.split())} words: {sentence[:50]!r}")
    for m in ISED.finditer(plain):
        if m[0].lower() not in ISE and (m[1] + "ise").lower() not in ISE:
            report.warn(29, at, f"{m[0]!r} is spelt -ize in Oxford spelling")
    for m in AMERICAN.finditer(plain):
        report.warn(29, at, f"{m[0]!r} is American spelling")
