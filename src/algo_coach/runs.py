"""The driver every model-backed run loop shares, and the limits it runs to.

Domain-free: a run loop decides what to ask and what to write, and this
decides only how many are in flight and when a run has broken rather than been
unlucky. Kept out of any one domain because the second loop that needed it
would otherwise import the first.
"""

from collections.abc import Callable, Iterator, Sequence
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
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

    Completion order, not the order asked in, which is safe for what the
    callers do with it. A claim ties with another only on `created_at`, broken
    by append order, and that decides between two claims on one attempt. A run
    makes at most one per attempt, so nothing a run writes can conflict with
    itself.

    Submission is bounded rather than all at once. A consumer that stops early,
    such as a run aborting on a rejected key, must not have paid for the tail.
    Closing the iterator cancels what has not started, and lets what is in
    flight finish, since an API call cannot be taken back.

    One worker is the serial path outright, not a pool of one. The ordinary run
    should not depend on a thread pool to be correct.
    """
    if concurrency <= 1:
        for item in items:
            try:
                yield item, work(item), None
            except Exception as exc:
                yield item, None, exc
        return

    queued = iter(items)
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        running = {pool.submit(work, item): item for item in islice(queued, concurrency)}
        try:
            while running:
                done, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    item = running.pop(future)
                    failure = future.exception()
                    yield item, (None if failure else future.result()), failure
                    running.update({pool.submit(work, nxt): nxt for nxt in islice(queued, 1)})
        finally:
            pool.shutdown(cancel_futures=True)
