from collections.abc import Iterable
from datetime import datetime
from typing import Protocol


class AttemptKeyed(Protocol):
    attempt_id: str
    created_at: datetime


def latest_by_attempt[R: AttemptKeyed](records: Iterable[R]) -> dict[str, R]:
    """The record that stands for each attempt, keyed by attempt id."""
    standing: dict[str, R] = {}
    for record in records:
        current = standing.get(record.attempt_id)
        # >=, so a tie on created_at goes to whatever was appended last.
        if current is None or record.created_at >= current.created_at:
            standing[record.attempt_id] = record
    return standing
