"""One solution, one case, and what the call produced.

Imports nothing from the package: the container backend runs this same script.
"""

import json
import signal
import sys
import time

RETURNED = "returned"
TIMEOUT = "timeout"
CRASHED = "crashed"


class Expired(Exception):
    """Its own exception, so a solution catching `Exception` cannot swallow the
    cap."""


def encode(value):
    # must stay the encoder `encoding.as_json` uses, or a return would be
    # decided differently by where it ran
    return json.dumps(value, sort_keys=True)


def execute(code, args, cap_ms):
    # the cap times the `solve` call alone; interpreter start and the module's
    # top level are the parent timer's to catch
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
        # a return JSON cannot encode is the solution's fault, not a wrong
        # answer
        return {"outcome": CRASHED, "value": None, "elapsed_ms": elapsed}
    return {"outcome": RETURNED, "value": encoded, "elapsed_ms": elapsed}


def _expire(signum, frame):
    raise Expired


def _since(started):
    return round((time.perf_counter() - started) * 1000)


def main():
    request = json.loads(sys.stdin.read())
    result = execute(request["code"], request["args"], request["cap_ms"])
    # to a file rather than stdout, which belongs to the solution
    with open(sys.argv[1], "w") as handle:
        json.dump(result, handle)


if __name__ == "__main__":
    main()
