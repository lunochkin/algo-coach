"""Rule 24: a `text` fence holds a drawing, and a drawing sits in one. Rule
25: a line of code fits a phone."""

import re

from algo_coach.knowledge.authoring.course import Course, Report, where
from algo_coach.knowledge.authoring.lessons import DIAGRAM

FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.S | re.M)
# a layout: columns aligned by spaces, arrows, an underline, an ordering
DRAWN = re.compile(DIAGRAM.pattern + r"|\S {2,}\S|->|[→←⇒▲▼✓✗]|\|=|[~^]{3}| < .* < ", re.M)
WIDE = 60
# a module written by concept holds a question's code to what a phone shows
NARROW = 40
LONGEST = 12
BOX = re.compile(r"[─│┌┐└┘├┤┬┴┼═║╔╗╚╝╭╮╰╯]")
# a tool's own output may hold them, as `uv tree` prints
HOLDS_BOX = ("text", "output", "console")


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


def box_drawing(course: Course, report: Report) -> None:
    for slug, text in course.lessons.items():
        fences = list(FENCE.finditer(text))
        if m := _in_prose(text, fences):
            at = f"lessons/{slug}.md {_line(text, m.start())} of the prose"
            report.error(24, at, _boxed(m[0]))
        for f in fences:
            if f[1] not in HOLDS_BOX and (m := BOX.search(f[2])):
                report.error(24, f"lessons/{slug}.md {_line(text, f.start())}", _boxed(m[0]))
    for q in course.questions:
        detail = q.get("detail", {})
        for name, value in (
            ("prompt", q.get("prompt")),
            ("code", q.get("code")),
            ("example", detail.get("example")),
            ("mechanism", detail.get("mechanism")),
        ):
            if isinstance(value, str) and (m := BOX.search(value)):
                report.error(24, f"{where(q)} {name}", _boxed(m[0]))


def _in_prose(text: str, fences: list[re.Match[str]]) -> re.Match[str] | None:
    spans = [(f.start(), f.end()) for f in fences]
    prose = (m for m in BOX.finditer(text) if not any(a <= m.start() < b for a, b in spans))
    return next(prose, None)


def _boxed(char: str) -> str:
    return f"{char!r} draws outside a `text` block: a structure is Mermaid, a table is markdown"


def _wide(code: str, limit: int = WIDE) -> str | None:
    over = [len(line) for line in code.splitlines() if len(line) > limit]
    if not over:
        return None
    lines = "line" if len(over) == 1 else "lines"
    return f"{len(over)} {lines} over {limit} characters, the longest {max(over)}"


def widths(course: Course, report: Report) -> None:
    narrow = NARROW if course.concepts else WIDE
    for q in course.questions:
        for name, code in (
            ("code", q.get("code")),
            ("example", q.get("detail", {}).get("example")),
        ):
            if isinstance(code, str) and (found := _wide(code, narrow)):
                report.warn(25, f"{where(q)} {name}", found)
        lines = len(str(q.get("code", "")).strip().splitlines())
        if course.concepts and lines > LONGEST:
            report.warn(25, f"{where(q)} code", f"{lines} lines, over {LONGEST}")
    # a fence naming a language or `output` wraps; a `text` one is a drawing,
    # and a `mermaid` one is drawn to the screen's width
    for slug, text in course.lessons.items():
        for m in FENCE.finditer(text):
            if m[1] and m[1] not in ("text", "mermaid") and (found := _wide(m[2])):
                report.warn(25, f"lessons/{slug}.md {_line(text, m.start())}", found)
