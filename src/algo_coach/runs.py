"""The driver every model-backed run loop shares, and the limits it runs to.

Domain-free: a run loop decides what to ask and what to write, and this
decides only how many are in flight and when a run has broken rather than been
unlucky. Kept out of any one domain because the second loop that needed it
would otherwise import the first.
"""

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from itertools import islice

# Consecutive failures that mean the run is broken rather than unlucky. A
# refusal or a rate limit hits one attempt; a rejected key or a spent quota
# hits every one, and reporting that per attempt buries it.
ABORT_AFTER = 3

# One call at a time. A backlog run is minutes of waiting on a network, so the
# default is the cautious one and the caller raises it: the binding limit is
# input tokens per minute, not requests, since every call carries the code and
# the criteria and thinks before it answers.
CONCURRENCY = 1


def as_answered[T, R](
    work: Callable[[T], R],
    items: Sequence[T],
    *,
    concurrency: int = CONCURRENCY,
) -> Iterator[tuple[T, R | None, Exception | None]]:
    """Run `work` over `items`, yielding each as it finishes.

    One group's worth of `as_answered_grouped`, which is where the behaviour
    and its reasons are written down.
    """
    yield from as_answered_grouped(work, {None: items}, concurrency=concurrency)


def as_answered_grouped[K, T, R](
    work: Callable[[T], R],
    streams: Mapping[K, Iterable[T]],
    *,
    concurrency: int = CONCURRENCY,
) -> Iterator[tuple[T, R | None, Exception | None]]:
    """Run `work` over every group at once, yielding each item as it finishes.

    `concurrency` is the budget of one key, not of the run. What meters a
    request is the deployment answering it, so two keys are two limits and a
    cap over the run as a whole would throttle whichever endpoint is not the
    bottleneck. A key is refilled only from its own stream, so a slow group can
    neither starve its neighbours nor borrow from them.

    Completion order, not the order asked in, which is safe for what the
    callers do with it. A claim ties with another only on `created_at`, broken
    by append order, and that decides between two claims on one attempt. A run
    makes at most one per attempt, so nothing a run writes can conflict with
    itself.

    Submission is bounded rather than all at once. A consumer that stops early,
    such as a run aborting on a rejected key, must not have paid for the tail.
    Closing the iterator cancels what has not started, and lets what is in
    flight finish, since an API call cannot be taken back.

    A stream is drawn from lazily, one item at a time, and that is how a caller
    gives up on part of a group without touching the rest of it. A stream that
    stops yielding is never drawn from again, and every draw happens after the
    previous answer was consumed — so a caller deciding mid-run reads its own
    state on the consuming thread, with nothing to lock.

    A single group at one worker is the serial path outright, not a pool of
    one. The ordinary run should not depend on a thread pool to be correct.
    Several groups always use a pool, since running them together is the point.
    """
    queues = {key: iter(stream) for key, stream in streams.items()}

    if len(queues) <= 1 and concurrency <= 1:
        for queue in queues.values():
            for item in queue:
                try:
                    yield item, work(item), None
                except Exception as exc:
                    yield item, None, exc
        return

    with ThreadPoolExecutor(max_workers=concurrency * max(len(queues), 1)) as pool:
        running: dict[Future[R], tuple[K, T]] = {}
        for key, queue in queues.items():
            running |= {pool.submit(work, item): (key, item) for item in islice(queue, concurrency)}
        try:
            while running:
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    key, item = running.pop(future)
                    failure = future.exception()
                    yield item, (None if failure else future.result()), failure
                    # From the stream that answered, never from another: the
                    # budget belongs to the deployment, so borrowing across
                    # keys would exceed one endpoint's while another idled.
                    running |= {
                        pool.submit(work, nxt): (key, nxt) for nxt in islice(queues[key], 1)
                    }
        finally:
            pool.shutdown(cancel_futures=True)
