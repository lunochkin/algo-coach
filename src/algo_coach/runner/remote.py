"""A run in the broker's container, over HTTP: the same JSON in and out.

`corpus.md` keeps the comparison above this boundary, so a request carries the
code, the arguments and the cap, and never what a case expects.
"""

from collections.abc import Sequence
from typing import Any

import httpx

# the variable naming the broker. Without it a submission runs in the local
# subprocess
BROKER = "ALGO_COACH_BROKER"

# what a verification stores for a run the broker answered. The image is
# pinned, so the interpreter is the container's rather than this process's
RUNNER = "container/cpython-3.14"

# the broker's own bounds, copied rather than imported: the process holding the
# container runtime's socket loads no engine code, so nothing imports it back
CASE_SLACK_MS = 3000
STARTUP_MS = 10_000
WAIT_SECONDS = 30

# the transport a test answers on, standing in for a broker and its container
TRANSPORT: httpx.BaseTransport | None = None


class RemoteFault(RuntimeError):
    """The broker answered no result, which says nothing about the solution."""


def request(
    code: str,
    args: Sequence[Sequence[Any]],
    cap_ms: int,
    repeats: Sequence[int] | None,
    stop_early: bool,
) -> dict[str, Any]:
    """What the broker is sent. No field carries what a case expects."""
    return {
        "code": code,
        "args": [list(one) for one in args],
        "cap_ms": cap_ms,
        "repeats": list(repeats) if repeats is not None else None,
        "stop_early": stop_early,
    }


def brokered(base: str, body: dict[str, Any]) -> list[dict[str, Any]]:
    """One run, and the case each line of the answer holds."""
    waited = _timeout(len(body["args"]), body["cap_ms"])
    try:
        with httpx.Client(base_url=base, transport=TRANSPORT, timeout=waited) as client:
            answer = client.post("/run", json=body)
    except httpx.HTTPError as error:
        raise RemoteFault(f"the broker at {base} answered nothing: {error}") from error
    if not answer.is_success:
        raise RemoteFault(f"the broker answered {answer.status_code}: {answer.text[:500]}")
    return answer.json()["cases"]


def _timeout(cases: int, cap_ms: int) -> float:
    # the broker's own deadline, the wait it admits a run within, and a second
    # for the request itself
    return (cases * (cap_ms + CASE_SLACK_MS) + STARTUP_MS) / 1000 + WAIT_SECONDS + 1
