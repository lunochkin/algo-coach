import argparse
import sys
from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from algo_coach.calls import Retry
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Attempt, MachineProvenance, SiteOutcome


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


def counter(index: int, total: int) -> str:
    return f"[{index:>{len(str(total))}}/{total}]"


def clipped(text: str, width: int) -> str:
    return f"{text[:width]:<{width}}"


def progress(index: int, total: int, *cells: str, verdict: str) -> None:
    """One line per item, on stderr and flushed: a call takes seconds."""
    print(f"{counter(index, total)} {' '.join(cells)}  {verdict}", file=sys.stderr, flush=True)


def named(reason: str | None, names: Sequence[str], *, none: str) -> str:
    """A run's verdict on one item: the failure, what it named, or that it
    named nothing."""
    if reason is not None:
        return f"! {reason}"
    return " ".join(names) or f"— {none}"


class RunOutcome(Protocol):
    aborted: bool
    failed: Sequence[object]

    @property
    def written(self) -> int: ...


def exit_on(parser: argparse.ArgumentParser, command: str, result: RunOutcome) -> None:
    """Failures were named as they happened; only the ends are here. Nonzero
    even where records landed: an aborted backlog was left unfinished."""
    if result.aborted:
        parser.exit(1, f"{command}: aborted after {ABORT_AFTER} consecutive failures\n")
    if result.failed and not result.written:
        parser.exit(1, f"{command}: nothing landed\n")


class Identified(Protocol):
    """What `one_of` needs of a record: an engine-minted id to match a prefix
    against."""

    id: str


def held(retry: Retry) -> str:
    """One wait. The endpoint too, since a cap is per endpoint rather than per
    model."""
    return (
        f"! {retry.status or 'failed'} {retry.model} @ {retry.pin}, "
        f"try {retry.tries}/{retry.of}, waiting {retry.pause:g}s"
    )


# how wide one case prints before it is cut. A separating input runs to
# thousands of elements, and the line is there to identify a case
CASE_WIDTH = 96


def configured(written: MachineProvenance | None) -> str:
    """What one step ran at, or that it never ran. The digest too: it is half
    of what a resume compares, and a prompt edit moves it alone."""
    if written is None:
        return "not taken"
    at = sampled(written.temperature)
    return f"{written.model}, effort {written.effort} @{at}, {written.prompt_hash} @ {written.pin}"


def shortened(args: object, expected: object) -> str:
    """Arguments and return on one line, cut to a width. A separating input
    runs to thousands of elements, where the line is here to identify a
    case."""
    line = f"{args} -> {expected}"
    return line if len(line) <= CASE_WIDTH else line[: CASE_WIDTH - 1] + "…"


def listing_code(name: str, code: str | None) -> list[str]:
    """One step's code, fenced. A step that never ran says so rather than
    printing an empty block."""
    if code is None:
        return [f"## {name}", "", "not written", ""]
    return [f"## {name}", "", "```python", code.rstrip(), "```", ""]


def left(one: SiteOutcome) -> str:
    """One site outcome: its gate, then the counters that are not zero. Every
    counter would print three zeroes for the sites that carry none."""
    parts = [f"{one.site:<15} {one.model}"]
    if one.gate is not None:
        parts.append(f"gate {one.gate}{f': {one.detail}' if one.detail else ''}")
    for name in ("mutants", "survived", "killed", "won", "offered", "misdeclared"):
        if getattr(one, name):
            parts.append(f"{name} {getattr(one, name)}")
    if one.rounds:
        parts.append(f"rounds {one.rounds}")
    if one.separating is not None:
        parts.append(f"separating at {one.separating}")
    if one.unseparated is not None:
        parts.append(f"unseparated: {one.unseparated}")
    if one.largest is not None:
        parts.append(f"up to {one.largest}")
    return "  ".join(parts)


def one_of[T: Identified](
    stored: Sequence[T], wanted: str, parser: argparse.ArgumentParser, kind: str
) -> T:
    """The record that id names, by prefix: an id is 32 hex characters, and a
    debugging read should not need all of them."""
    matched = [one for one in stored if one.id.startswith(wanted)]
    if not matched:
        parser.exit(1, f"{kind}: no {kind} {wanted}\n")
    if len(matched) > 1:
        named = ", ".join(one.id for one in matched)
        parser.exit(2, f"{kind}: {wanted} names {len(matched)} {kind}s: {named}\n")
    return matched[0]
