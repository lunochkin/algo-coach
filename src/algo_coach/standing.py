"""Which record stands where several answer one question: the latest, and
between writers the one that knew most."""

from collections.abc import Callable, Hashable, Iterable, Sequence
from datetime import datetime
from operator import attrgetter
from typing import Protocol


class Stamped(Protocol):
    created_at: datetime


def latest_by[K: Hashable, R: Stamped](records: Iterable[R], key: Callable[[R], K]) -> dict[K, R]:
    """The last record per key. `>=`, so a tie on `created_at` goes to whatever
    was appended last."""
    standing: dict[K, R] = {}
    for record in records:
        current = standing.get(key(record))
        if current is None or record.created_at >= current.created_at:
            standing[key(record)] = record
    return standing


def standing[K: Hashable, R: Stamped](
    records: Iterable[R],
    key: Callable[[R], K],
    *,
    by_what_each_knew: Sequence[object],
    source: Callable[[R], object] = attrgetter("source"),
) -> dict[K, R]:
    """The record that stands per key: each writer's latest, weakest writer
    first, so a stronger one's overwrites it however late the weaker's."""
    records = list(records)
    stands: dict[K, R] = {}
    for writer in by_what_each_knew:
        stands |= latest_by((one for one in records if source(one) == writer), key)
    return stands


__all__ = ["Stamped", "latest_by", "standing"]
