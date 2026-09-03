import argparse
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


# What a temperature nobody set prints as: a named arm, not an empty cell.
UNSET = "default"


def sampled(temperature: float | None) -> str:
    return UNSET if temperature is None else str(temperature)


def chosen(
    temperature: str,
    parser: argparse.ArgumentParser,
    *,
    command: str,
    fallback: float | None,
) -> float | None:
    """`None` only where `default` was asked for by name; the flag left off
    takes the built-in temperature."""
    if not temperature:
        return fallback
    if temperature == UNSET:
        return None
    try:
        return float(temperature)
    except ValueError:
        parser.exit(2, f"{command}: --temperature {temperature} is not a number or {UNSET!r}\n")
        raise


def held(retry: Retry) -> str:
    """One wait. The endpoint too, since a cap is per endpoint rather than per model."""
    return (
        f"! {retry.status or 'failed'} {retry.model} @ {retry.pin}, "
        f"try {retry.tries}/{retry.of}, waiting {retry.pause:g}s"
    )
