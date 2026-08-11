"""The driver both run loops share, on the path where calls overlap."""

import threading
import time

import pytest

from algo_coach.claims import as_answered


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
