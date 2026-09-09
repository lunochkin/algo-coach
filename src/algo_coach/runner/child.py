"""One solution, one case, and what the call produced.

Imports nothing from the package: the container backend runs this same script.
"""

import json
import signal
import sys
import time
from types import FrameType
from typing import Any

RETURNED = "returned"
TIMEOUT = "timeout"
CRASHED = "crashed"


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
        compiled = compile(code, "<solution>", "exec")
        exec(compiled, {"__name__": "__solution__"})
    except BaseException:
        return {"outcome": CRASHED, "value": None, "elapsed_ms": None}

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
    except BaseException:
        return {"outcome": CRASHED, "value": None, "elapsed_ms": round(elapsed * 1000)}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

    measured = round(elapsed * 1000)
    try:
        encoded = encode(value)
    except TypeError, ValueError:
        # a return JSON cannot encode is the solution's fault, not a wrong
        # answer
        return {"outcome": CRASHED, "value": None, "elapsed_ms": measured}
    return {"outcome": RETURNED, "value": encoded, "elapsed_ms": measured}


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
