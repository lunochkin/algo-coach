from collections.abc import Iterable
from datetime import datetime
from operator import attrgetter
from typing import Protocol

from algo_coach.standing import latest_by


class AttemptKeyed(Protocol):
    attempt_id: str
    created_at: datetime


def latest_by_attempt[R: AttemptKeyed](records: Iterable[R]) -> dict[str, R]:
    """The one reader over the three attempt-keyed records, as `log.md` gives."""
    return latest_by(records, attrgetter("attempt_id"))
