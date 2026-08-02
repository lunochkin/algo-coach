from collections.abc import Iterable
from datetime import datetime
from typing import Protocol


class AttemptKeyed(Protocol):
    """An append-only record about one attempt, superseded by a later one."""

    attempt_id: str
    created_at: datetime


def latest_by_attempt[R: AttemptKeyed](records: Iterable[R]) -> dict[str, R]:
    """The record that stands for each attempt, keyed by attempt id.

    Latest by `created_at`, append order breaking a tie. A later record
    supersedes the earlier one whole rather than merging with it, so the
    superseded ones stay in the log and never reach a reader.

    Claims, self-labels and diagnoses are all read this way: the shape is the
    log's, not any one record's.
    """
    standing: dict[str, R] = {}
    for record in records:
        current = standing.get(record.attempt_id)
        if current is None or record.created_at >= current.created_at:
            standing[record.attempt_id] = record
    return standing
