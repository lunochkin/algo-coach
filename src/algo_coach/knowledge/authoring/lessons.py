"""Rule 2: a lesson's code block runs on its own and matches its shown
output. Rule 24: a `text` fence draws."""

import concurrent.futures as cf
import hashlib
import os
import re
from collections import defaultdict
from urllib.parse import urlsplit, urlunsplit

from algo_coach.knowledge.authoring.course import Course, Report, norm
from algo_coach.knowledge.authoring.execution import Runs, absent, last_exception
from algo_coach.knowledge.authoring.snippets import TOOLS

BLOCK = re.compile(r"```python\n(.*?)```(\s*```(?:output|text)\n(.*?)```)?", re.S)
TEXT = re.compile(r"^```text\n(.*?)^```", re.S | re.M)
DIAGRAM = re.compile(r"[─│┌┐└┘├┤┬┴┼▶◀•═║]|^\s+[/\\|]\s", re.M)
TOOL_OUTPUT = re.compile(r"^(\$ |\S+\.py:\d+(:\d+)?:? |Success: no issues)", re.M)
AWAIT = re.compile(r"^(await |async (with|for) )", re.M)
POSTGRES = re.compile(r"\b(psycopg|asyncpg)\b|postgresql(\+\w+)?://")

# a lesson's slug, the block's number, its code and the output shown under it
type Block = tuple[str, int, str, str | None]
type LessonRan = tuple[str, int, str, str]


def lesson_blocks(course: Course) -> list[Block]:
    blocks: list[Block] = []
    for slug, text in course.lessons.items():
        for n, m in enumerate(BLOCK.finditer(text), 1):
            blocks.append((slug, n, m[1], m[3]))
    return blocks


def text_fences(course: Course, report: Report) -> None:
    for slug, text in course.lessons.items():
        for m in TEXT.finditer(text):
            if not DIAGRAM.search(m[1]):
                line = text.count("\n", 0, m.start()) + 1
                report.warn(
                    24,
                    f"lessons/{slug}.md line {line}",
                    "a text block draws nothing: fence output as `output`",
                )


def as_async(code: str) -> str:
    body = "".join("    " + line + "\n" for line in code.splitlines())
    return "import asyncio\nasync def __main():\n" + body + "asyncio.run(__main())\n"


def lesson_run(runs: Runs, code: str, before: str) -> LessonRan:
    """A block alone, then wrapped for top-level await, then after the
    lesson's earlier blocks: how it ran, and its result."""
    attempts = [("alone", code)]
    if AWAIT.search(code):
        attempts.append(("alone", as_async(code)))
    if before:
        attempts.append(("after earlier blocks", before + "\n" + code))
        if AWAIT.search(before + code):
            attempts.append(("after earlier blocks", as_async(before + "\n" + code)))
    for how, text in attempts:
        status, out, err = runs.run(text)
        if status == 0:
            return how, status, out, err
    return "alone", *runs.run(code)


def matches(shown: str, ran: LessonRan) -> bool:
    how, status, out, err = ran
    raised = err.strip().splitlines()[-1] if status and err.strip() else ""
    want = norm(shown)
    candidates = {norm(out), norm(out + raised), norm(out + err), norm(err + out)}
    if how != "alone":
        return any(c.endswith(want) for c in candidates)
    return want in candidates


def postgres_server() -> str | None:
    """The Postgres server TEST_DATABASE_URL names, as a libpq URL."""
    url = os.environ.get("TEST_DATABASE_URL")
    return re.sub(r"^postgresql\+\w+://", "postgresql://", url) if url else None


def on_postgres(code: str, slug: str, n: int, server: str) -> str:
    """A Postgres block, pointed at a database of its own on the test server.
    Lesson blocks name the conventional `app` database three ways."""
    parts = urlsplit(server)
    name = f"lesson_{hashlib.sha256(f'{slug}:{n}'.encode()).hexdigest()[:10]}"
    target = urlunsplit(parts._replace(path=f"/{name}"))
    netloc = parts.netloc
    code = code.replace('"dbname=app"', repr(target))
    code = re.sub(
        r"(postgresql(\+\w+)?://)app@localhost/app", lambda m: f"{m[1]}{netloc}/{name}", code
    )
    if re.search(r"\bDSN\b", code) and not re.search(r"^DSN\s*=", code, re.M):
        code = f"DSN = {target!r}\n" + code
    setup = (
        "import psycopg as _pg\n"
        f"with _pg.connect({server!r}, autocommit=True) as _c:\n"
        f"    _c.execute('DROP DATABASE IF EXISTS {name} WITH (FORCE)')\n"
        f"    _c.execute('CREATE DATABASE {name}')\n"
    )
    return setup + code


def lessons_run(course: Course, report: Report, pool: cf.Executor, runs: Runs) -> int:
    skipped = course.skip.get("lesson-block", {})
    server = postgres_server()
    jobs: dict[cf.Future[LessonRan], Block] = {}
    before: dict[str, str] = defaultdict(str)
    for slug, n, code, shown in lesson_blocks(course):
        earlier = before[slug]
        before[slug] += code + "\n"
        if f"{slug}:{n}" in skipped or TOOLS.search(code) or absent(code, course, report):
            continue
        if POSTGRES.search(code):
            if not server:
                report.error(
                    2,
                    f"lessons/{slug}.md block {n}",
                    "needs a Postgres server: set TEST_DATABASE_URL",
                )
                continue
            code, earlier = on_postgres(code, slug, n, server), ""
        if shown is not None and (DIAGRAM.search(shown) or TOOL_OUTPUT.search(shown)):
            shown = None
        jobs[pool.submit(lesson_run, runs, code, earlier)] = (slug, n, code, shown)
    for future in cf.as_completed(jobs):
        _judge(jobs[future], future.result(), report)
    return len(jobs)


def _judge(block: Block, ran: LessonRan, report: Report) -> None:
    slug, n, code, shown = block
    how, status, out, err = ran
    where = f"lessons/{slug}.md block {n}"
    raised = last_exception(err) if status else ""
    if status == -1:
        report.error(2, where, "timed out")
    elif shown is None and status and raised not in code:
        report.error(2, where, f"raises {raised} and shows no output")
    elif shown is not None and not matches(shown, ran):
        report.error(2, where, f"shown {shown.strip()[:50]!r}, got {(out or err).strip()[:50]!r}")
    elif how != "alone":
        report.warn(2, where, "runs only after the lesson's earlier blocks")
