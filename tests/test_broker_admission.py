import asyncio
import threading
import time

import httpx

from algo_coach.broker import create_app
from algo_coach.broker.container import Finished

RUN = {"code": "def solve(n):\n    return n * 2\n", "args": [[1]], "cap_ms": 3000}
RETURNED = b'{"outcome": "returned", "value": "2", "elapsed_ms": 0}\n'


class Slow:
    """Answers each run after `seconds`, and keeps how many ran at once."""

    def __init__(self, seconds: float, returncode: int = 0) -> None:
        self.seconds = seconds
        self.returncode = returncode
        self.runs = 0
        self.most = 0
        self._active = 0
        self._counting = threading.Lock()

    def __call__(self, argv: list[str], stdin: bytes, limit: int, seconds: float) -> Finished:
        with self._counting:
            self.runs += 1
            self._active += 1
            self.most = max(self.most, self._active)
        time.sleep(self.seconds)
        with self._counting:
            self._active -= 1
        return Finished("exited", self.returncode, RETURNED, b"")


def _stopped(_name: str) -> None:
    """Stands in for killing a container, which no run here expires into."""


def _cleared() -> None:
    """Stands in for removing leftover containers, which only a started broker
    does."""


async def posted(slow: Slow, runs: int, wait_seconds: float = 30) -> list[httpx.Response]:
    """`runs` runs sent at once, each as its own request."""
    app = create_app(slow, _stopped, _cleared, wait_seconds=wait_seconds)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://broker") as client:
        return list(await asyncio.gather(*(client.post("/run", json=RUN) for _ in range(runs))))


async def test_runs_arriving_together_run_one_at_a_time():
    """A verdict is wall clock against the cap, so a run beside another measures
    the contention between them."""
    slow = Slow(0.2)

    responses = await posted(slow, 3)

    assert [each.status_code for each in responses] == [200, 200, 200]
    assert (slow.runs, slow.most) == (3, 1)


async def test_a_run_waiting_past_the_bound_is_refused_without_running():
    """An unbounded wait reads to the user as a sandbox that hung."""
    slow = Slow(1.0)

    responses = await posted(slow, 2, wait_seconds=0.1)

    assert sorted(each.status_code for each in responses) == [200, 503]
    (refused,) = (each for each in responses if each.status_code == 503)
    assert refused.headers["retry-after"] == "1"
    assert slow.runs == 1


async def test_a_failed_run_still_admits_the_next():
    """The admission is released on every path, or one fault would refuse
    every later run."""
    failing = Slow(0.0, returncode=125)
    app = create_app(failing, _stopped, _cleared)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://broker") as client:
        first = await client.post("/run", json=RUN)
        second = await client.post("/run", json=RUN)

    assert (first.status_code, second.status_code) == (500, 500)
    assert failing.runs == 2
