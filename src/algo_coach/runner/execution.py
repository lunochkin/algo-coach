"""The one call the executor sits behind: JSON in, JSON out, no callable."""

import ast
import contextlib
import json
import os
import select
import signal
import subprocess
import sys
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

# slack on the parent's own timer, beyond the cap the child enforces. It covers
# interpreter start and catches a child stuck where no Python-level timer
# fires.
STARTUP_MS = 2000

# the backend and the interpreter, as a verification stores them. Opaque to
# every reader, so the format is this module's alone
RUNNER = f"subprocess/{sys.implementation.name}-{sys.version_info.major}.{sys.version_info.minor}"

CHILD = Path(__file__).with_name("child.py")

# how many children are started before the batch they answer. Interpreter start
# is what a case costs, and starting them together spends it on several cores
# at once. Bounded rather than the whole set: a run of a thousand cases would
# otherwise hold a thousand idle interpreters
BATCH = 16


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
        for start in range(0, len(cases), BATCH):
            batch = list(
                zip(cases[start : start + BATCH], counts[start : start + BATCH], strict=True)
            )
            # started together and fed one at a time: the cases stay
            # sequential, so nothing a run measures is timed against another
            # case
            waiting = [
                _started(Path(work) / f"{start + index}.json") for index in range(len(batch))
            ]
            stopped = False
            for (one, count), (child, path) in zip(batch, waiting, strict=True):
                if stopped:
                    # killed and reaped: a child left unwaited is a zombie, and
                    # its open pipe a warning the suite treats as an error
                    _kill(child.pid)
                    child.communicate()
                    continue
                result = _answered(child, path, code, one, cap_ms, count)
                results.append(result)
                # never at a returned value, however wrong: the backend is not
                # told what a case expects
                stopped = stop_early and not result.returned
            if stopped:
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


def _started(result_path: Path) -> tuple[subprocess.Popen[str], Path]:
    """One child, blocked on the request it has not been sent.

    It carries no case yet: what it is waiting through is its own interpreter
    start, which is what a case costs where the solution is fast.
    """
    child = subprocess.Popen(
        [sys.executable, str(CHILD), str(result_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        # its own session, so a solution's own children die with it
        start_new_session=True,
    )
    return child, result_path


def _answered(
    child: subprocess.Popen[str],
    result_path: Path,
    code: str,
    args: list[Any],
    cap_ms: int,
    repeats: int = 1,
) -> CaseRun:
    # one case per child: `corpus.md` requires that no case observes another
    request = json.dumps({"code": code, "args": args, "cap_ms": cap_ms, "repeats": repeats})
    assert child.stdin is not None
    # a child that died before reading the whole request is read from how it
    # died, below
    with contextlib.suppress(BrokenPipeError):
        child.stdin.write(request)
    with contextlib.suppress(BrokenPipeError):
        child.stdin.close()
    try:
        if not _exited(child.pid, (cap_ms + STARTUP_MS) / 1000):
            return CaseRun(RunOutcome.TIMEOUT)
    finally:
        # on every path: what the solution spawned outlives a child that
        # reported its own timeout. Reaped after, so an exit code is kept
        _kill(child.pid)
        child.wait()
    return _reported(result_path, child.returncode)


def _exited(pid: int, timeout: float) -> bool:
    """Whether the child exited within the timeout, woken by the exit itself.
    `Popen.wait` polls instead, sleeping up to 50 ms past a child that already
    finished, which every case paid."""
    if sys.platform == "linux":
        watched = os.pidfd_open(pid)
        try:
            ready, _, _ = select.select([watched], [], [], timeout)
        finally:
            os.close(watched)
        return bool(ready)
    if sys.platform == "darwin":
        queue = select.kqueue()
        try:
            exit = select.kevent(
                pid,
                filter=select.KQ_FILTER_PROC,
                flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
                fflags=select.KQ_NOTE_EXIT,
            )
            return bool(queue.control([exit], 1, timeout))
        except ProcessLookupError:
            # exited before it was watched
            return True
        finally:
            queue.close()
    raise RunnerError(f"no way to wait on a child on {sys.platform}")


def _kill(pid: int) -> None:
    """The group, not the process: `start_new_session` made the child its
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
