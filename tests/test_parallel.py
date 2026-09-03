import threading
import time

import pytest

from algo_coach.claims import as_answered, as_answered_grouped


def test_serial_when_one_worker_runs_on_the_calling_thread():
    """One worker is the serial path outright, not a pool of one: the ordinary
    run must not depend on a thread pool to be correct."""
    caller = threading.current_thread()
    threads = []

    for _ in as_answered(lambda _: threads.append(threading.current_thread()), [1, 2, 3]):
        pass

    assert threads == [caller, caller, caller]


@pytest.mark.parametrize("concurrency", [1, 4])
def test_every_item_is_answered_exactly_once(concurrency):
    seen = [
        item
        for item, _, _ in as_answered(
            lambda item: item * 2, list(range(20)), concurrency=concurrency
        )
    ]

    assert sorted(seen) == list(range(20))


@pytest.mark.parametrize("concurrency", [1, 4])
def test_the_result_travels_with_its_own_item(concurrency):
    """Completion order is not the order asked in, so a caller reading results
    positionally would attribute one attempt's verdict to another."""
    answered = {
        item: result
        for item, result, _ in as_answered(
            lambda item: item * 2, list(range(20)), concurrency=concurrency
        )
    }

    assert answered == {item: item * 2 for item in range(20)}


@pytest.mark.parametrize("concurrency", [1, 4])
def test_a_failure_is_returned_beside_its_item_not_raised(concurrency):
    """One attempt's problem: a run that died on the first refusal would report
    nothing about the rest."""

    def work(item: int) -> int:
        if item == 2:
            raise ValueError("refused")
        return item

    failures = {
        item: failure for item, _, failure in as_answered(work, [1, 2, 3], concurrency=concurrency)
    }

    assert failures[1] is None and failures[3] is None
    assert isinstance(failures[2], ValueError)


def test_calls_overlap():
    """The point of the whole thing: four calls in flight take about as long as
    one, not four."""
    started = threading.Barrier(4, timeout=5)

    def work(_: int) -> None:
        started.wait()  # times out unless four run at once

    list(as_answered(work, list(range(4)), concurrency=4))


def test_stopping_early_leaves_the_tail_unasked():
    """A consumer that stops — a run aborting on a rejected key — must not have
    paid for what it never reached."""
    asked = []
    lock = threading.Lock()

    def work(item: int) -> int:
        with lock:
            asked.append(item)
        time.sleep(0.01)
        return item

    for _ in as_answered(work, list(range(50)), concurrency=2):
        break

    assert len(asked) < 50


def test_no_more_than_the_asked_for_calls_run_at_once():
    live = 0
    peak = 0
    lock = threading.Lock()

    def work(_: int) -> None:
        nonlocal live, peak
        with lock:
            live += 1
            peak = max(peak, live)
        time.sleep(0.01)
        with lock:
            live -= 1

    list(as_answered(work, list(range(12)), concurrency=3))

    assert peak <= 3


def test_a_key_never_exceeds_its_own_budget():
    """The budget is per deployment, since that is what meters the requests.
    A cap over the run as a whole would throttle the endpoints that are not
    the bottleneck."""
    live: dict[str, int] = {}
    peak: dict[str, int] = {}
    lock = threading.Lock()

    def work(item: tuple[str, int]) -> None:
        key, _ = item
        with lock:
            live[key] = live.get(key, 0) + 1
            peak[key] = max(peak.get(key, 0), live[key])
        time.sleep(0.01)
        with lock:
            live[key] -= 1

    groups = {key: [(key, index) for index in range(8)] for key in ("a", "b", "c")}
    list(as_answered_grouped(work, groups, concurrency=2))

    assert peak == {"a": 2, "b": 2, "c": 2}


def test_the_groups_genuinely_overlap():
    """One group at a time is what this replaces. The barrier clears only if
    every group has a call in flight at once."""
    ready = threading.Barrier(3, timeout=5)

    def work(item: tuple[str, int]) -> str:
        ready.wait()
        return item[0]

    groups = {key: [(key, 0)] for key in ("a", "b", "c")}

    answered = [result for _, result, _ in as_answered_grouped(work, groups, concurrency=1)]

    assert sorted(answered) == ["a", "b", "c"]


def test_every_item_across_every_group_is_answered_once():
    groups = {"a": [("a", index) for index in range(6)], "b": [("b", index) for index in range(4)]}

    seen = [item for item, _, _ in as_answered_grouped(lambda item: item, groups, concurrency=3)]

    assert sorted(seen) == sorted(groups["a"] + groups["b"])


def test_the_result_still_travels_with_its_own_item():
    """Completion order is not the order asked in, and now two groups' answers
    interleave — a caller reading positionally would attribute one
    configuration's verdict to another."""
    groups = {"a": [("a", index) for index in range(5)], "b": [("b", index) for index in range(5)]}

    for item, result, _ in as_answered_grouped(
        lambda item: f"{item[0]}{item[1]}", groups, concurrency=2
    ):
        assert result == f"{item[0]}{item[1]}"


def test_a_failure_comes_back_beside_its_item_and_its_group_continues():
    """One refusal is one item's problem. The group behind it must still be
    read, and so must every other group."""
    broken = RuntimeError("refused")

    def work(item: tuple[str, int]) -> str:
        if item == ("a", 0):
            raise broken
        return "ok"

    groups = {"a": [("a", index) for index in range(3)], "b": [("b", 0)]}

    answered = list(as_answered_grouped(work, groups, concurrency=1))

    failures = [(item, failure) for item, _, failure in answered if failure is not None]
    assert failures == [(("a", 0), broken)]
    assert len(answered) == 4


def test_a_stream_that_stops_yielding_is_not_drawn_from_again():
    """Abort is per configuration, and a group carries several of them.
    Giving up on one must not stop the deployment it shares — which the
    caller says by returning from its own stream."""
    asked: list[tuple[str, int]] = []
    lock = threading.Lock()
    dropped = set()

    def work(item: tuple[str, int]) -> str:
        with lock:
            asked.append(item)
        return item[0]

    def stream(key: str, count: int):
        for index in range(count):
            if key in dropped:
                return
            yield key, index

    for item, _, _ in as_answered_grouped(
        work, {"a": stream("a", 10), "b": stream("b", 4)}, concurrency=1
    ):
        if item[0] == "a":
            dropped.add("a")

    assert len([one for one in asked if one[0] == "a"]) == 1
    assert len([one for one in asked if one[0] == "b"]) == 4


def test_stopping_early_leaves_every_group_s_tail_unasked():
    asked = []
    lock = threading.Lock()

    def work(item: tuple[str, int]) -> int:
        with lock:
            asked.append(item)
        time.sleep(0.01)
        return item[1]

    groups = {key: [(key, index) for index in range(25)] for key in ("a", "b")}

    for _ in as_answered_grouped(work, groups, concurrency=2):
        break

    assert len(asked) < 50


def test_one_group_at_one_worker_is_still_the_serial_path():
    """`as_answered` is this with a single group, and its guarantee is that an
    ordinary run does not depend on a thread pool to be correct."""
    caller = threading.current_thread()
    threads = []

    for _ in as_answered_grouped(
        lambda _: threads.append(threading.current_thread()), {"only": [1, 2, 3]}
    ):
        pass

    assert threads == [caller, caller, caller]
