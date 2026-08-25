from datetime import datetime

from algo_coach.calls import Retry
from algo_coach.schema import Attempt


def age(when: datetime | None, now: datetime) -> str:
    if when is None:
        return "never"
    # Clamped: a submission stamped later today is not negatively old.
    days = max((now - when).days, 0)
    return f"{when:%Y-%m-%d} ({days}d)"


def verdict(attempt: Attempt) -> str:
    return "solved" if attempt.solved else "unsolved"


# What a temperature nobody set is called. A named arm rather than an empty
# cell: the provider's own default is a fact about the reading, and it compares
# only with itself.
UNSET = "default"


def sampled(temperature: float | None) -> str:
    return UNSET if temperature is None else str(temperature)


def held(retry: Retry) -> str:
    """One wait, named by what caused it and how long it will last.

    The endpoint rather than the model alone: a cap is per endpoint, and two
    configurations sharing one are held by the same limit.
    """
    return (
        f"! {retry.status or 'failed'} {retry.model} @ {retry.pin}, "
        f"try {retry.tries}/{retry.of}, waiting {retry.pause:g}s"
    )
