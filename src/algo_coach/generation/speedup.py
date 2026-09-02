"""The smallest input under which the reference exceeds the cap and the
canonical does not.

Run only where the template claims a speedup. Backtracking and exhaustive
search are their own optimum, so no input separates the two solutions there,
and a missing separation says nothing about them.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from algo_coach.generation.checks import CAP_MS
from algo_coach.runner import RunOutcome, as_json, run

# the most a stored case may weigh, arguments and expected value together.
# `corpus.md` gives the reason and what a case over it costs
CEILING = 65_536


class Missing(StrEnum):
    """Why a search found no separating input. Named rather than a boolean:
    only the first is a defect where a speedup was claimed."""

    REFERENCE_FINISHED = "reference_finished"
    REFERENCE_CRASHED = "reference_crashed"
    CANONICAL_FAILED = "canonical_failed"
    INPUT_TOO_LARGE = "input_too_large"


@dataclass(frozen=True)
class Searched:
    """The separating input, or why there was none. The two are exclusive."""

    size: int | None = None
    args: list[Any] = field(default_factory=list)
    # what the child measured at that size. The reference's is absent where it
    # exceeded the measuring cap rather than merely the drill loop's
    canonical_ms: int | None = None
    reference_ms: int | None = None
    missing: Missing | None = None

    @property
    def found(self) -> bool:
        return self.missing is None


def search(
    make: Callable[[int], Sequence[Any]],
    *,
    canonical: str,
    reference: str,
    cap_ms: int,
    largest: int,
    smallest: int = 1,
    measure_ms: int = CAP_MS,
    ceiling: int = CEILING,
) -> Searched:
    """Double until the reference exceeds `cap_ms`, then halve to the smallest
    size that does. `largest` is what the statement's constraints allow: an
    input above it separates nothing, because no solution owes an answer there.
    """
    # measured well above the cap, so one run reads as a time rather than as a
    # timeout, and no later search re-runs what this one already measured
    if measure_ms <= cap_ms:
        raise ValueError("the measuring cap sits above the cap being separated")

    if smallest > largest:
        raise ValueError("the smallest size the search starts at is within the constraints")

    under, over, over_ms, capped = smallest, None, None, False
    size = smallest
    while True:
        args = list(make(size))
        # stopped before the run rather than after it: an input over the
        # ceiling is one no case can carry, whatever the reference does on it
        if _weighs(args) > ceiling:
            capped = True
            break
        exceeded, elapsed = _reference(reference, args, cap_ms=cap_ms, measure_ms=measure_ms)
        if exceeded is None:
            return Searched(missing=Missing.REFERENCE_CRASHED)
        if exceeded:
            over, over_ms = size, elapsed
            break
        under = size
        if size >= largest:
            break
        # clamped rather than doubled past it: the largest legal input is the
        # one size a search that found nothing has to have tried
        size = min(size * 2, largest)

    if over is None:
        return Searched(missing=Missing.INPUT_TOO_LARGE if capped else Missing.REFERENCE_FINISHED)

    # runtime is taken to grow with the size: the halving needs it, and nothing
    # short of running every size in between would establish it
    while over - under > 1:
        middle = (under + over) // 2
        exceeded, elapsed = _reference(
            reference, make(middle), cap_ms=cap_ms, measure_ms=measure_ms
        )
        if exceeded is None:
            return Searched(missing=Missing.REFERENCE_CRASHED)
        if exceeded:
            over, over_ms = middle, elapsed
        else:
            under = middle

    return _settled(
        list(make(over)),
        over,
        canonical=canonical,
        cap_ms=cap_ms,
        reference_ms=over_ms,
        ceiling=ceiling,
    )


def _settled(
    args: list[Any],
    size: int,
    *,
    canonical: str,
    cap_ms: int,
    reference_ms: int | None,
    ceiling: int,
) -> Searched:
    # the canonical is run under the cap it has to beat rather than the
    # measuring one: what the case asserts is that this solution answers there
    [ran] = run(canonical, [args], cap_ms=cap_ms)
    if not ran.returned:
        return Searched(missing=Missing.CANONICAL_FAILED)
    # the returned value weighs on the case as the arguments do
    if _weighs(args) + _weighs(ran.value) > ceiling:
        return Searched(missing=Missing.INPUT_TOO_LARGE)
    return Searched(size=size, args=args, canonical_ms=ran.elapsed_ms, reference_ms=reference_ms)


def _weighs(value: Any) -> int:
    return len(as_json(value).encode())


def _reference(
    code: str,
    args: Sequence[Any],
    *,
    cap_ms: int,
    measure_ms: int,
) -> tuple[bool | None, int | None]:
    """Whether the reference exceeds `cap_ms` at this size, and what it took.
    `None` where it crashed, which is neither."""
    [ran] = run(code, [list(args)], cap_ms=measure_ms)
    if ran.outcome is RunOutcome.TIMEOUT:
        return True, None
    if not ran.returned:
        return None, None
    return ran.elapsed_ms > cap_ms, ran.elapsed_ms


__all__ = ["CEILING", "Missing", "Searched", "search"]
