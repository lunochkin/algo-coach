"""One solution, one case, and what the call produced.

Imports nothing from the package: the broker sends this script to a run's
container, and `main` is that container's entry process.
"""

import contextlib
import json
import linecache
import os
import resource
import select
import signal
import sys
import time
import traceback
from types import FrameType
from typing import Any

RETURNED = "returned"
TIMEOUT = "timeout"
CRASHED = "crashed"

# the filename the solution is compiled under, and the frames a crash report
# keeps
SOLUTION = "<solution>"

# slack on the entry's own timer, beyond the cap the child enforces. The local
# runner's STARTUP_MS, which this script cannot import
SLACK_MS = 2000

# a case's own address space, under the container's memory limit. A case that
# exhausts memory then raises in its own child, where the container's limit
# alone has the host kill the container and every later case with it
CASE_MEMORY_BYTES = 320 << 20


class Expired(Exception):
    """Its own exception, so a solution catching `Exception` cannot swallow the
    cap."""


def encode(value: object) -> str:
    # must stay the encoder `encoding.as_json` uses, or a return would be
    # decided differently by where it ran
    return json.dumps(value, sort_keys=True)


def execute(code: str, args: list[Any], cap_ms: int, repeats: int = 1) -> dict[str, Any]:
    # the cap times the `solve` calls alone; interpreter start and the module's
    # top level are the parent timer's to catch
    try:
        compiled = compile(code, SOLUTION, "exec")
        exec(compiled, {"__name__": "__solution__"})
    except BaseException as error:
        return crashed(None, described(error, code))

    signal.signal(signal.SIGALRM, _expire)
    signal.setitimer(signal.ITIMER_REAL, cap_ms / 1000)
    elapsed = 0.0
    value = None
    try:
        for _ in range(repeats):
            # a fresh module per call, so a memo left in a global cannot answer
            # the next one. It costs microseconds and is outside the timing,
            # as the module's top level is on a single call
            namespace: dict[str, Any] = {"__name__": "__solution__"}
            exec(compiled, namespace)
            solve = namespace["solve"]
            started = time.perf_counter()
            value = solve(*args)
            elapsed += time.perf_counter() - started
    except Expired:
        return {"outcome": TIMEOUT, "value": None, "elapsed_ms": round(elapsed * 1000)}
    except BaseException as error:
        return crashed(round(elapsed * 1000), described(error, code))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

    measured = round(elapsed * 1000)
    try:
        encoded = encode(value)
    except TypeError, ValueError:
        # a return JSON cannot encode is the solution's fault, not a wrong
        # answer
        kind = type(value).__name__
        return crashed(measured, f"solve returned a {kind}, which JSON cannot encode")
    return {"outcome": RETURNED, "value": encoded, "elapsed_ms": measured}


def crashed(elapsed_ms: int | None, error: str) -> dict[str, Any]:
    return {"outcome": CRASHED, "value": None, "elapsed_ms": elapsed_ms, "error": error}


def described(error: BaseException, code: str) -> str:
    """The exception as a traceback prints it, over the solution's own frames.
    The child's frames name no line the solver wrote."""
    # a compiled string has no file to read its lines back from
    linecache.cache[SOLUTION] = (len(code), None, code.splitlines(keepends=True), SOLUTION)
    report = traceback.TracebackException.from_exception(error)
    report.stack = traceback.StackSummary.from_list(
        [frame for frame in report.stack if frame.filename == SOLUTION]
    )
    return "".join(report.format())


def _expire(_signum: int, _frame: FrameType | None) -> None:
    raise Expired


def case(code: str, args: list[Any], cap_ms: int, repeats: int, result_path: str) -> None:
    """One case in a child the local runner forked for it."""
    _isolate()
    result = execute(code, args, cap_ms, repeats)
    with open(result_path, "w") as handle:
        json.dump(result, handle)


def _isolate() -> None:
    """Its own session, so a solution's own children die with it, and no
    stream the solution can print to."""
    os.setsid()
    silent = os.open(os.devnull, os.O_RDWR)
    for stream in (0, 1, 2):
        os.dup2(silent, stream)


# run once before a run's first case and thrown away: the first case after a
# container boots otherwise runs on pages and caches gVisor has not yet touched
WARM_UP = "def solve():\n    return 0\n"


def main() -> None:
    """A whole run from standard input, one result line per case on standard
    output."""
    request = json.loads(sys.stdin.read())
    cases: list[list[Any]] = request["args"]
    counts: list[int] = request.get("repeats") or [1] * len(cases)
    if cases:
        forked(WARM_UP, [], request["cap_ms"], 1)
    for args, repeats in zip(cases, counts, strict=True):
        result = forked(request["code"], args, request["cap_ms"], repeats)
        sys.stdout.write(json.dumps(result) + "\n")
        sys.stdout.flush()
        # never at a returned value, however wrong: nothing here knows what a
        # case expects
        if request.get("stop_early") and result["outcome"] != RETURNED:
            break


def forked(code: str, args: list[Any], cap_ms: int, repeats: int) -> dict[str, Any]:
    """One case in a child of its own, its result read back over a pipe."""
    read, write = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(read)
            _isolate()
            _limit_memory()
            result = execute(code, args, cap_ms, repeats)
            with os.fdopen(write, "w") as channel:
                channel.write(json.dumps(result) + "\n")
        finally:
            # never back into the entry's loop, whatever raised
            os._exit(0)

    os.close(write)
    try:
        line = _line(read, time.monotonic() + (cap_ms + SLACK_MS) / 1000)
    finally:
        os.close(read)
        # on every path: what the solution spawned outlives a child that
        # reported, and holds the pipe open besides
        for kill in (os.killpg, os.kill):
            with contextlib.suppress(ProcessLookupError, PermissionError):
                kill(pid, signal.SIGKILL)
        _, status = os.waitpid(pid, 0)

    if line is None:
        return {"outcome": TIMEOUT, "value": None, "elapsed_ms": None}
    if line:
        return json.loads(line)
    exitcode = os.waitstatus_to_exitcode(status)
    if exitcode < 0:
        return crashed(None, f"killed by signal {-exitcode}")
    raise RuntimeError(f"the child wrote no result and exited {exitcode}")


def _limit_memory() -> None:
    # suppressed where the platform refuses the limit, which leaves the
    # container's own limit as it was
    with contextlib.suppress(OSError, ValueError):
        resource.setrlimit(resource.RLIMIT_AS, (CASE_MEMORY_BYTES, CASE_MEMORY_BYTES))


def _line(fd: int, deadline: float) -> bytes | None:
    """The child's result line, empty where the pipe closed without one, or
    `None` where the deadline passed first."""
    # up to the newline rather than to the pipe's close: a process the solution
    # forked holds the pipe open past the child's own exit
    chunks: list[bytes] = []
    while (left := deadline - time.monotonic()) > 0:
        ready, _, _ = select.select([fd], [], [], left)
        if not ready:
            break
        chunk = os.read(fd, 1 << 16)
        chunks.append(chunk)
        if not chunk or chunk.endswith(b"\n"):
            return b"".join(chunks)
    return None


if __name__ == "__main__":
    main()
