"""The one call the executor sits behind.

JSON in and JSON out. No path and no callable in the signature, so a remote
sandbox takes the same payload as the local subprocess: code as text,
arguments as values, a cap in milliseconds.

The backend is never told what a case expects. Comparison stays above this
boundary, so the rule deciding a case cannot vary by where the code ran, and a
sandbox is never handed the answer.
"""

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

# What the parent waits, beyond the cap the child enforces itself. It covers
# interpreter start, which the cap excludes, and exists for a child stuck
# where no Python-level timer fires.
STARTUP_MS = 2000

CHILD = Path(__file__).with_name("child.py")


class RunnerError(RuntimeError):
    """The runner's own fault, raised rather than recorded.

    A subprocess that fails to start, or one that exits cleanly having written
    nothing, says nothing about the solution. A stored `CRASHED` would discard
    a sound problem over the runner's own defect.
    """


class RunOutcome(StrEnum):
    """How one call went, in the words a backend can say.

    Three rather than four: `PASSED` and `WRONG` are a comparison against an
    expected value, and nothing below this boundary has one.
    """

    RETURNED = "returned"
    TIMEOUT = "timeout"
    CRASHED = "crashed"


@dataclass(frozen=True)
class CaseRun:
    """One call of `solve`: what it produced, and what the child measured.

    `value` is the decoded return, and is meaningless unless the call
    returned. `elapsed_ms` is absent where the child measured nothing — code
    that never reached `solve`, or a timeout the parent's own timer decided.
    """

    outcome: RunOutcome
    value: Any = None
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
    """Run `code` once per argument list, and report what each call produced.

    The whole set in one call rather than one call per case: a per-case
    boundary is one network round trip per case once the executor is remote.

    Under `stop_early` the run stops at the first crash or timeout, and never
    at a returned value however wrong it looks — the backend is not told what
    a case expects. The result is then shorter than the set, and the mutation
    loop is what wants that where the attempt path wants every case decided.
    """
    if cap_ms <= 0:
        raise ValueError("a cap of nothing decides nothing about the solution")

    cases = [list(one) for one in args]
    if not defines_solve(code):
        # Read from the tree, so a module whose import does not terminate is
        # rejected rather than reaching the cap. A verdict rather than an
        # error: Phase 8 reads this path for an attempt, and a submission with
        # a syntax error is the ordinary case.
        #
        # Every case, whatever `stop_early` says. The verdict is a fact about
        # the code rather than about a case, so nothing ran and there is
        # nothing to stop at.
        return [CaseRun(RunOutcome.CRASHED) for _ in cases]

    results: list[CaseRun] = []
    for one in cases:
        result = _one_case(code, one, cap_ms)
        results.append(result)
        if stop_early and not result.returned:
            break
    return results


def defines_solve(code: str) -> bool:
    """Whether the module defines a module-level `solve`.

    The entry point is fixed rather than stored, so a solution defining
    anything else is not a solution to any problem.
    """
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


def _one_case(code: str, args: list[Any], cap_ms: int) -> CaseRun:
    """One case per subprocess. Module-level state must not carry from one
    case to the next: a solution memoising in a global would otherwise answer
    one case from a cache built for another, and a wrong key would pass."""
    request = json.dumps({"code": code, "args": args, "cap_ms": cap_ms})
    with TemporaryDirectory() as work:
        result_path = Path(work) / "result.json"
        child = subprocess.Popen(
            [sys.executable, str(CHILD), str(result_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            # its own session, so a solution that spawned a child of its own
            # is killed with it rather than left running
            start_new_session=True,
        )
        try:
            child.communicate(request, timeout=(cap_ms + STARTUP_MS) / 1000)
        except subprocess.TimeoutExpired:
            _kill(child.pid)
            child.communicate()
            return CaseRun(RunOutcome.TIMEOUT)
        finally:
            # Whatever the solution spawned outlives the child that reported
            # its own timeout, so the group is killed on every path rather
            # than only where the parent's timer fired.
            _kill(child.pid)
        return _reported(result_path, child.returncode)


def _kill(pid: int) -> None:
    """The group, not the process. `start_new_session` makes the child a group
    leader, so its own id is the group's."""
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pid, signal.SIGKILL)


def _reported(path: Path, returncode: int) -> CaseRun:
    """What the child wrote, or how it died where it wrote nothing.

    A signal is `CRASHED`, which is where a segfault and a kill under memory
    pressure land. Anything else is the runner's own fault.
    """
    try:
        reported = json.loads(path.read_text())
    except FileNotFoundError, json.JSONDecodeError:
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
