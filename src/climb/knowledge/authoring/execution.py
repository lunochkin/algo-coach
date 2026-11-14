"""Running a snippet in a fresh interpreter, with each result kept under what
decided it."""

import functools
import hashlib
import importlib.metadata
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from climb.knowledge.authoring.course import Course, Report

TIMEOUT = 20
TOOL_TIMEOUT = 120
WARNED = re.compile(r"^\S*:\d+: (\w+Warning): ", re.M)

type Ran = tuple[int, str, str]


@functools.cache
def installed() -> set[str]:
    return set(importlib.metadata.packages_distributions())


@functools.cache
def identity(python: str) -> str:
    """What decides a run besides its code: the interpreter's build, and for
    the project's own the installed distributions."""
    if python == sys.executable:
        dists = sorted(
            f"{d.metadata['Name']}=={d.version}" for d in importlib.metadata.distributions()
        )
        return sys.version + "\n".join(dists)
    done = subprocess.run(
        [python, "-c", "import sys; print(sys.version)"], capture_output=True, text=True
    )
    return done.stdout


def _key(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()


def _without(cwd: str, text: str) -> str:
    # the directory's name is random, and a warning or a traceback prints it
    here = re.compile("|".join(re.escape(p) for p in {cwd, os.path.realpath(cwd)}))
    return here.sub("<cwd>", text)


class Runs:
    """The results kept from earlier runs, and the runs this check executed."""

    def __init__(self, kept: dict[str, Any] | None = None) -> None:
        self.cache: dict[str, Any] = dict(kept or {})
        self.executed: list[str] = []

    def run(self, code: str, python: str = sys.executable) -> Ran:
        """Code in a fresh isolated interpreter, in an empty directory."""
        key = _key(identity(python), str(TIMEOUT), code)
        if key not in self.cache:
            self.cache[key] = list(self._execute(code, python))
        status, out, err = self.cache[key]
        return status, out, err

    def _execute(self, code: str, python: str) -> Ran:
        self.executed.append(python)
        with tempfile.TemporaryDirectory() as cwd:
            Path(cwd, "main.py").write_text(code)
            try:
                done = subprocess.run(
                    [python, "-I", "main.py"],
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT,
                    cwd=cwd,
                    env={**os.environ, "PYTHONHASHSEED": "0"},
                )
            except subprocess.TimeoutExpired:
                return -1, "", "timeout"
            return done.returncode, _without(cwd, done.stdout), _without(cwd, done.stderr)

    def tool(self, code: str, argv: list[str], filename: str) -> str:
        """A type checker's or a linter's output on code saved as `filename`."""
        key = _key(identity(sys.executable), "tool", str(argv), filename, code)
        if key not in self.cache:
            self.executed.append(argv[0])
            with tempfile.TemporaryDirectory() as cwd:
                Path(cwd, filename).write_text(code)
                self.cache[key] = [tool_output(argv, cwd), ""]
        return self.cache[key][0]

    def kept[T](self, key: str, what: str, compute: Callable[[], T]) -> T:
        if key not in self.cache:
            self.executed.append(what)
            self.cache[key] = compute()
        return self.cache[key]


def tool_output(argv: list[str], cwd: str) -> str:
    """What a tool prints run in `cwd`, with the directory's name removed."""
    exe = (
        [str(Path(sys.executable).parent / "pyright")]
        if argv[0] == "pyright"
        else [sys.executable, "-m", argv[0]]
    )
    done = subprocess.run(
        exe + argv[1:], capture_output=True, text=True, timeout=TOOL_TIMEOUT, cwd=cwd
    )
    root = os.path.realpath(cwd)
    return (done.stdout + done.stderr).replace(root + "/", "").replace(cwd + "/", "")


def last_exception(stderr: str) -> str:
    """The name of the exception a traceback ends on, skipping warnings."""
    for line in reversed(stderr.strip().splitlines()):
        if WARNED.match(line):
            continue
        if m := re.match(r"([A-Za-z_][\w.]*)(:|$)", line):
            return m[1].rsplit(".", 1)[-1]
    return ""


def raised_by(status: int, err: str) -> str:
    return last_exception(err) if status else ""


def third_party(code: str) -> set[str]:
    names = re.findall(r"^\s*(?:from|import)\s+([A-Za-z_]\w*)", code, re.M)
    return {n for n in names if n not in sys.stdlib_module_names and n != "__future__"}


def absent(code: str, course: Course, report: Report) -> bool:
    """Whether the code imports a module no installed distribution provides.
    The report counts each such module, so a skipped snippet is never silent."""
    gone = third_party(code) - installed()
    for name in gone - course.fixtures:
        report.missing[name] += 1
    if gone and gone <= course.fixtures:
        report.made_up += 1
    return bool(gone)
