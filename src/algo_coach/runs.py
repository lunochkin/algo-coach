"""The driver every model-backed run loop shares, kept domain-free."""

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from itertools import islice

# Consecutive failures that mean broken rather than unlucky: a rejected key
# hits every attempt.
ABORT_AFTER = 3

# The binding limit is input tokens per minute, not requests.
CONCURRENCY = 1


def as_answered[T, R](
    work: Callable[[T], R],
    items: Sequence[T],
    *,
    concurrency: int = CONCURRENCY,
) -> Iterator[tuple[T, R | None, Exception | None]]:
    yield from as_answered_grouped(work, {None: items}, concurrency=concurrency)


@dataclass
class Bounded[T, R]:
    """The answers of one run, numbered as they arrive and stopped after
    `ABORT_AFTER` consecutive failures. `aborted` says whether they were.

    Consecutive by the order answered, so with calls in flight a broken key
    costs up to `concurrency` failures rather than `ABORT_AFTER`. The failure
    that reached the bound is still yielded: the caller records it, and the
    stream ends after.
    """

    answers: Iterable[tuple[T, R | None, Exception | None]]
    aborted: bool = False

    def __iter__(self) -> Iterator[tuple[int, T, R | None, Exception | None]]:
        consecutive = 0
        for index, (item, answer, failure) in enumerate(self.answers, start=1):
            yield index, item, answer, failure
            if failure is None:
                consecutive = 0
                continue
            consecutive += 1
            if consecutive == ABORT_AFTER:
                self.aborted = True
                return


def as_answered_grouped[K, T, R](
    work: Callable[[T], R],
    streams: Mapping[K, Iterable[T]],
    *,
    concurrency: int = CONCURRENCY,
) -> Iterator[tuple[T, R | None, Exception | None]]:
    """Run `work` over every group at once, yielding each item as it finishes.

    `concurrency` is one key's budget, not the run's: the deployment answering
    meters the request. Order is completion, not submission, which is bounded
    so a consumer that stops early has not paid for the tail. Each draw happens
    after the previous answer was consumed, so a caller needs no lock.
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
                    if failure is not None and not isinstance(failure, Exception):
                        # a KeyboardInterrupt in a worker is the run's, not the item's
                        raise failure
                    yield item, (None if failure else future.result()), failure
                    # From the stream that answered, never another: the budget
                    # belongs to the deployment.
                    running |= {
                        pool.submit(work, nxt): (key, nxt) for nxt in islice(queues[key], 1)
                    }
        finally:
            pool.shutdown(cancel_futures=True)
