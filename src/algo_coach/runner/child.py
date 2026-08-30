"""One solution, one case, and what the call produced.

Standalone by rule: it imports nothing from the package, because the container
backend runs this same script. One protocol, written once — a request on
stdin, a result on the path in argv.

Stdout belongs to the solution. A solution that prints would corrupt the
channel, so the result never travels on it.
"""

import json
import signal
import sys
import time

RETURNED = "returned"
TIMEOUT = "timeout"
CRASHED = "crashed"


class Expired(Exception):
    """The cap fired around `solve`. Its own exception, so a solution catching
    `Exception` broadly cannot swallow the cap."""


def encode(value):
    """A value as the case will hold it, with the encoder every backend
    shares. Encoding here rather than above the boundary is what keeps the
    same return from being decided differently by where it ran."""
    return json.dumps(value, sort_keys=True)


def execute(code, args, cap_ms):
    """The module, then `solve` under the cap.

    The cap is wall clock around the call alone. Interpreter start and the
    module's own top level are outside it, since both move with the machine's
    load and the parent's timer is what catches a module that never finishes.
    """
    namespace = {"__name__": "__solution__"}
    try:
        exec(compile(code, "<solution>", "exec"), namespace)  # noqa: S102 - the subject
        solve = namespace["solve"]
    except BaseException:
        return {"outcome": CRASHED, "value": None, "elapsed_ms": None}

    signal.signal(signal.SIGALRM, _expire)
    signal.setitimer(signal.ITIMER_REAL, cap_ms / 1000)
    started = time.perf_counter()
    try:
        value = solve(*args)
    except Expired:
        return {"outcome": TIMEOUT, "value": None, "elapsed_ms": _since(started)}
    except BaseException:
        return {"outcome": CRASHED, "value": None, "elapsed_ms": _since(started)}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)

    elapsed = _since(started)
    try:
        encoded = encode(value)
    except TypeError, ValueError:
        # The fault is the solution's rather than the case's. `WRONG` would
        # file it beside an answer that was computed and is merely incorrect.
        return {"outcome": CRASHED, "value": None, "elapsed_ms": elapsed}
    return {"outcome": RETURNED, "value": encoded, "elapsed_ms": elapsed}


def _expire(signum, frame):
    raise Expired


def _since(started):
    return round((time.perf_counter() - started) * 1000)


def main():
    request = json.loads(sys.stdin.read())
    result = execute(request["code"], request["args"], request["cap_ms"])
    with open(sys.argv[1], "w") as handle:
        json.dump(result, handle)


if __name__ == "__main__":
    main()
