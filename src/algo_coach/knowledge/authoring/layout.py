"""Rule 24: a `text` fence holds a drawing. Rule 25: a line of code fits a
phone."""

import re

from algo_coach.knowledge.authoring.course import Course, Report, where
from algo_coach.knowledge.authoring.lessons import DIAGRAM

FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.S | re.M)
# a layout: columns aligned by spaces, arrows, an underline, an ordering
DRAWN = re.compile(DIAGRAM.pattern + r"|\S {2,}\S|->|[→←⇒▲▼✓✗]|\|=|[~^]{3}| < .* < ", re.M)
WIDE = 60


def _line(text: str, at: int) -> str:
    return f"line {text.count(chr(10), 0, at) + 1}"


def text_fences(course: Course, report: Report) -> None:
    for slug, text in course.lessons.items():
        for m in FENCE.finditer(text):
            if m[1] == "text" and not DRAWN.search(m[2]):
                report.warn(
                    24,
                    f"lessons/{slug}.md {_line(text, m.start())}",
                    "a text block draws nothing: fence output as `output`",
                )


def _wide(code: str) -> str | None:
    over = [len(line) for line in code.splitlines() if len(line) > WIDE]
    if not over:
        return None
    lines = "line" if len(over) == 1 else "lines"
    return f"{len(over)} {lines} over {WIDE} characters, the longest {max(over)}"


def widths(course: Course, report: Report) -> None:
    for q in course.questions:
        for name, code in (
            ("code", q.get("code")),
            ("example", q.get("detail", {}).get("example")),
        ):
            if isinstance(code, str) and (found := _wide(code)):
                report.warn(25, f"{where(q)} {name}", found)
    # a fence naming a language or `output` wraps, and a `text` one is a drawing
    for slug, text in course.lessons.items():
        for m in FENCE.finditer(text):
            if m[1] and m[1] != "text" and (found := _wide(m[2])):
                report.warn(25, f"lessons/{slug}.md {_line(text, m.start())}", found)
