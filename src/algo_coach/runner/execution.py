"""The one call the executor sits behind: JSON in, JSON out, no callable."""

import ast
import contextlib
import json
import os
import signal
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

# slack on the parent's own timer, beyond the cap the child enforces. It covers
# interpreter start and catches a child stuck where no Python-level timer fires.
STARTUP_MS = 2000

CHILD = Path(__file__).with_name("child.py")

# how many children are started before the batch they answer. Interpreter start
# is what a case costs, and starting them together spends it on several cores
# at once. Bounded rather than the whole set: a run of a thousand cases would
# otherwise hold a thousand idle interpreters
BATCH = 16


class RunnerError(RuntimeError):
    """The runner's own fault, raised rather than recorded as a verdict."""


class RunOutcome(StrEnum):
    # three rather than four: nothing below this boundary knows what was expected
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

    @property
    def returned(self) -> bool:
        return self.outcome is RunOutcome.RETURNED


def run(
    code: str,
    args: Sequence[Sequence[Any]],
    *,
    cap_ms: int,
    stop_early: bool = False,
) -> list[CaseRun]:
    # the whole set in one call: a per-case boundary is a round trip per case
    # once the executor is remote
    if cap_ms <= 0:
        raise ValueError("a cap of nothing decides nothing about the solution")

    cases = [list(one) for one in args]
    if not defines_solve(code):
        # every case, whatever `stop_early` says: nothing ran, so there is
        # nothing to stop at
        return [CaseRun(RunOutcome.CRASHED) for _ in cases]

    results: list[CaseRun] = []
    with TemporaryDirectory() as work:
        for start in range(0, len(cases), BATCH):
            batch = cases[start : start + BATCH]
            # started together and fed one at a time: the cases stay sequential,
            # so nothing a run measures is timed against another case
            waiting = [
                _started(Path(work) / f"{start + index}.json") for index in range(len(batch))
            ]
            stopped = False
            for one, (child, path) in zip(batch, waiting, strict=True):
                if stopped:
                    _kill(child.pid)
                    continue
                result = _answered(child, path, code, one, cap_ms)
                results.append(result)
                # never at a returned value, however wrong: the backend is not
                # told what a case expects
                stopped = stop_early and not result.returned
            if stopped:
                break
    return results


def defines_solve(code: str) -> bool:
    # read from the tree: a module whose import does not terminate must not
    # reach the cap
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    return any(_defines(node) for node in tree.body)


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
) -> CaseRun:
    # one case per child: `corpus.md` requires that no case observes another
    request = json.dumps({"code": code, "args": args, "cap_ms": cap_ms})
    try:
        child.communicate(request, timeout=(cap_ms + STARTUP_MS) / 1000)
    except subprocess.TimeoutExpired:
        _kill(child.pid)
        child.communicate()
        return CaseRun(RunOutcome.TIMEOUT)
    finally:
        # on every path: what the solution spawned outlives a child that
        # reported its own timeout
        _kill(child.pid)
    return _reported(result_path, child.returncode)


def _kill(pid: int) -> None:
    """The group, not the process: `start_new_session` made the child its leader."""
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
            return CaseRun(RunOutcome.CRASHED)
        raise RunnerError(f"the child wrote no result and exited {returncode}") from None

    outcome = RunOutcome(reported["outcome"])
    encoded = reported["value"]
    return CaseRun(
        outcome,
        json.loads(encoded) if encoded is not None else None,
        reported["elapsed_ms"],
    )
