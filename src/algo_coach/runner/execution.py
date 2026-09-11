"""The one call the executor sits behind: JSON in, JSON out, no callable."""

import ast
import contextlib
import json
import multiprocessing
import os
import select
import signal
import sys
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from algo_coach.runner import child

# slack on the parent's own timer, beyond the cap the child enforces. It covers
# the child's start and catches a child stuck where no Python-level timer
# fires.
STARTUP_MS = 2000

# the backend and the interpreter, as a verification stores them. Opaque to
# every reader, so the format is this module's alone
RUNNER = f"subprocess/{sys.implementation.name}-{sys.version_info.major}.{sys.version_info.minor}"

# a child per case, forked from a server that imported the child's module once:
# an interpreter start per case cost some 40ms before the solution ran. The
# server imports `__main__` too, or every child would run the console script's
# imports again. A plain module run with `python -m` is not preloaded, and pays
# that per case
_FORKS = multiprocessing.get_context("forkserver")
_FORKS.set_forkserver_preload(["__main__", "algo_coach.runner.child"])


class RunnerError(RuntimeError):
    """The runner's own fault, raised rather than recorded as a verdict."""


class RunOutcome(StrEnum):
    # three rather than four: nothing below this boundary knows what was
    # expected
    RETURNED = "returned"
    TIMEOUT = "timeout"
    CRASHED = "crashed"


@dataclass(frozen=True)
class CaseRun:
    outcome: RunOutcome
    value: Any = None
    # absent where the child measured nothing: code that never reached `solve`,
    # or a timeout the parent's own timer decided
    elapsed_ms: int | None = None
    error: str | None = None  # what raised, on a crash alone

    @property
    def returned(self) -> bool:
        return self.outcome is RunOutcome.RETURNED


def run(
    code: str,
    args: Sequence[Sequence[Any]],
    *,
    cap_ms: int,
    repeats: Sequence[int] | None = None,
    stop_early: bool = False,
) -> list[CaseRun]:
    """One run per argument tuple. `repeats` says how many times `solve` is
    called on each, one entry per tuple, and the cap covers the sum. Absent is
    one call each, which is every case but a separating one."""
    # the whole set in one call: a per-case boundary is a round trip per case
    # once the executor is remote
    if cap_ms <= 0:
        raise ValueError("a cap of nothing decides nothing about the solution")

    cases = [list(one) for one in args]
    counts = list(repeats) if repeats is not None else [1] * len(cases)
    if len(counts) != len(cases):
        raise ValueError("a repeat count per argument tuple, or none at all")
    why = unrunnable(code)
    if why is not None:
        # every case, whatever `stop_early` says: nothing ran, so there is
        # nothing to stop at
        return [CaseRun(RunOutcome.CRASHED, error=why) for _ in cases]

    results: list[CaseRun] = []
    with TemporaryDirectory() as work:
        for index, (one, count) in enumerate(zip(cases, counts, strict=True)):
            result = _answered(Path(work) / f"{index}.json", code, one, cap_ms, count)
            results.append(result)
            # never at a returned value, however wrong: the backend is not told
            # what a case expects
            if stop_early and not result.returned:
                break
    return results


def defines_solve(code: str) -> bool:
    return unrunnable(code) is None


def unrunnable(code: str) -> str | None:
    """Why the code cannot reach `solve`, or `None` where it can."""
    # read from the tree: a module whose import does not terminate must not
    # reach the cap
    try:
        tree = ast.parse(code, "<solution>")
    except SyntaxError as error:
        return "".join(traceback.format_exception_only(error))
    if not any(_defines(node) for node in tree.body):
        return "no module-level `solve` is defined"
    return None


def _defines(node: ast.stmt) -> bool:
    match node:
        case ast.FunctionDef(name="solve") | ast.AsyncFunctionDef(name="solve"):
            return True
        case ast.Assign(targets=targets):
            return any(isinstance(one, ast.Name) and one.id == "solve" for one in targets)
        case ast.AnnAssign(target=ast.Name(id="solve"), value=value):
            return value is not None
        case _:
            return False


def _answered(
    result_path: Path,
    code: str,
    args: list[Any],
    cap_ms: int,
    repeats: int = 1,
) -> CaseRun:
    # one case per child: `corpus.md` requires that no case observes another
    process = _FORKS.Process(
        target=child.case, args=(code, args, cap_ms, repeats, str(result_path))
    )
    process.start()
    assert process.pid is not None
    try:
        # the sentinel is readable once the child exits, so nothing polls
        ready, _, _ = select.select([process.sentinel], [], [], (cap_ms + STARTUP_MS) / 1000)
        if not ready:
            return CaseRun(RunOutcome.TIMEOUT)
    finally:
        # on every path: what the solution spawned outlives a child that
        # reported its own timeout. Reaped after, so an exit code is kept
        _kill(process.pid)
        process.join()
    exitcode = process.exitcode
    process.close()
    assert exitcode is not None
    return _reported(result_path, exitcode)


def _kill(pid: int) -> None:
    """The group, not the process: the child made itself its session's
    leader."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pid, signal.SIGKILL)


def _reported(path: Path, returncode: int) -> CaseRun:
    """What the child wrote, or how it died where it wrote nothing."""
    try:
        reported = json.loads(path.read_text())
    except FileNotFoundError, json.JSONDecodeError:
        # a signal is where a segfault and an OOM kill land; anything else is
        # the runner's own fault
        if returncode < 0:
            return CaseRun(RunOutcome.CRASHED, error=f"killed by signal {-returncode}")
        raise RunnerError(f"the child wrote no result and exited {returncode}") from None

    outcome = RunOutcome(reported["outcome"])
    encoded = reported["value"]
    return CaseRun(
        outcome,
        json.loads(encoded) if encoded is not None else None,
        reported["elapsed_ms"],
        reported.get("error"),
    )
