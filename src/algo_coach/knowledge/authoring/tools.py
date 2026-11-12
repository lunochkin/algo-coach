"""Rule 4: a tool's output in a lesson is what the tool prints, in a block's
shown output and in a console transcript alike."""

import concurrent.futures as cf
import functools
import hashlib
import re
import shlex
import sys
import tempfile
from pathlib import Path

from algo_coach.knowledge.authoring.course import Course, Report
from algo_coach.knowledge.authoring.execution import Runs, identity, tool_output
from algo_coach.knowledge.authoring.lessons import lesson_blocks

DIAGNOSTIC = re.compile(
    r"^\s*(?:\S*/)?(\w+\.py):(\d+)(?::(\d+))?(?::| -) ?"
    r"(error|note|warning|information)?:? ?(.*?)\s*$"
)
RUFF = re.compile(r"^(?:\S*/)?(\w+\.py):(\d+):(\d+): ([A-Z]+\d+) (.*?)\s*$")
CUT = re.compile(r"\.\.\.|…|\[cut\]", re.I)
CONSOLE = re.compile(r"```(?:console|shell|bash|sh)\n(.*?)```", re.S)
TOOL_LINE = re.compile(r"^(ruff|mypy|pyright)\b")

# a command, the lines shown under it, and what the tool printed
type Replayed = tuple[str, str, str]


def diagnostics(text: str, root: str = "") -> list[str]:
    """A tool's report as lines a reader can compare: file, line, kind and
    message, whatever directory the tool was run in."""
    found: list[str] = []
    for line in text.replace(root + "/", "").splitlines():
        if m := RUFF.match(line):
            found.append(f"{m[1]}:{m[2]}:{m[3]}: {m[4]} {m[5]}")
        elif (m := DIAGNOSTIC.match(line)) and m[4]:
            found.append(f"{m[1]}:{m[2]}: {m[4]}: {m[5]}")
    return found


def tool_command(shown: str) -> tuple[list[str], str] | None:
    """The command a block's output came from: its `$` line, or the typing
    lessons' convention of mypy --strict on ex.py."""
    if m := re.search(r"^\$ ((mypy|pyright|ruff)\b.*)$", shown, re.M):
        argv = m[1].split()
        files = [a for a in argv if a.endswith(".py")]
        return argv, files[0] if files else "ex.py"
    if re.search(r"^\$ ", shown, re.M) or not diagnostics(shown):
        return None
    files = sorted({d.split(":")[0] for d in diagnostics(shown)})
    return ["mypy", "--strict", *files], files[0]


def _compare(report: Report, where: str, shown: str, out: str, command: str = "") -> None:
    want, got = diagnostics(shown), diagnostics(out)
    named = f"`{command[:40]}` " if command else ""
    width = 60 if command else 70
    if wrong := [d for d in want if d not in got]:
        report.error(4, where, f"{named}shows {wrong[0][:width]!r}, which the tool does not print")
    elif len(got) > len(want) and not CUT.search(shown):
        report.warn(
            4, where, f"{named}shows {len(want)} of the tool's {len(got)} lines, and marks no cut"
        )


def tool_outputs(course: Course, report: Report, pool: cf.Executor, runs: Runs) -> int:
    jobs: dict[cf.Future[str], tuple[str, int, str]] = {}
    for slug, n, code, shown in lesson_blocks(course):
        if shown and (command := tool_command(shown)):
            jobs[pool.submit(runs.tool, code, *command)] = (slug, n, shown)
    for future in cf.as_completed(jobs):
        slug, n, shown = jobs[future]
        _compare(report, f"lessons/{slug}.md block {n}", shown, future.result())
    return len(jobs)


def transcript(text: str) -> list[tuple[str, list[str]]]:
    """A console block as its commands, each with the lines shown under it."""
    steps: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("$ "):
            steps.append((line[2:], []))
        elif steps:
            steps[-1][1].append(line)
    return steps


def settings_above(text: str, at: int) -> str:
    """The tool settings a lesson gives in the toml block nearest above a
    transcript, which the transcript's commands read from pyproject.toml."""
    blocks = list(re.finditer(r"```toml\n(.*?)```", text[:at], re.S))
    if blocks and re.search(r"^\[tool\.(ruff|mypy|pyright)", blocks[-1][1], re.M):
        return blocks[-1][1]
    return ""


def replay(steps: list[tuple[str, list[str]]], settings: str = "") -> list[Replayed] | None:
    """Each tool command of a transcript with its shown and its real output.
    A `cat` writes the file it shows. None where a command reads a file the
    transcript never shows, so nothing can be compared."""
    results: list[Replayed] = []
    with tempfile.TemporaryDirectory() as cwd:
        if settings:
            Path(cwd, "pyproject.toml").write_text(settings)
        for line, shown in steps:
            command, _, note = line.partition("  # ")
            argv = shlex.split(command)
            if argv[0] == "cat" and len(argv) == 2:
                Path(cwd, argv[1]).write_text("\n".join(shown) + "\n")
            elif argv[0] == "cp" and len(argv) == 3:
                if not _copied(cwd, argv[1], argv[2]):
                    return None
            elif TOOL_LINE.match(command):
                files = [a for a in argv[1:] if a.endswith(".py") or Path(cwd, a).is_dir()]
                if not files or not all(Path(cwd, f).exists() for f in files):
                    return None
                if m := re.search(r"requires-python = \">=3\.(\d+)\"", note):
                    argv += ["--target-version", f"py3{m[1]}"]
                results.append((command, "\n".join(shown), tool_output(argv, cwd)))
    return results


def _copied(cwd: str, source: str, target: str) -> bool:
    to = Path(cwd, target)
    to.parent.mkdir(parents=True, exist_ok=True)
    if not Path(cwd, source).exists():
        return False
    to.write_text(Path(cwd, source).read_text())
    return True


def transcripts(course: Course, report: Report, runs: Runs) -> int:
    count = 0
    for slug, text in course.lessons.items():
        for n, m in enumerate(CONSOLE.finditer(text), 1):
            steps = transcript(m[1])
            if not any(TOOL_LINE.match(c) for c, _ in steps):
                continue
            count += 1
            settings = settings_above(text, m.start())
            key = "\0".join((identity(sys.executable), "transcript", settings, m[1]))
            replayed = runs.kept(
                hashlib.sha256(key.encode()).hexdigest(),
                "transcript",
                functools.partial(replay, steps, settings),
            )
            where = f"lessons/{slug}.md transcript {n}"
            if replayed is None:
                report.unreplayed.append(where)
                continue
            for command, shown, out in replayed:
                _compare(report, where, shown, out, command)
    return count
