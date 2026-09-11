"""One solution, one case, and what the call produced.

Imports nothing from the package: the container backend runs this same script.
"""

import json
import linecache
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


def main() -> None:
    request = json.loads(sys.stdin.read())
    result = execute(request["code"], request["args"], request["cap_ms"], request.get("repeats", 1))
    # to a file rather than stdout, which belongs to the solution
    with open(sys.argv[1], "w") as handle:
        json.dump(result, handle)


if __name__ == "__main__":
    main()
