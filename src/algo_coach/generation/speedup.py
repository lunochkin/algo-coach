"""The smallest input under which the naive solution exceeds the cap and the
canonical does not. Run only where the template claims a speedup.

Two solutions, two jobs: the naive one is the naive solution, and the reference settles
what the case at that size returns.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from functools import partial
from typing import Any

from algo_coach.generation.agreement import Disagreement, settle
from algo_coach.generation.checks import CAP_MS
from algo_coach.runner import RunOutcome, answered, run, weighs
from algo_coach.schema import MachineProvenance, SettledCase

# the cap a sitting judges a submission under, which is what the separating
# case is chosen against. Phase 8 reads it; generation's own cap sits above it
DRILL_CAP_MS = 2_000

# the most a stored case may weigh, arguments and expected value together.
# `corpus.md` gives the reason and what a case over it costs
CEILING = 1_048_576


class Missing(StrEnum):
    """Why a search stored no separating case. Named rather than a boolean,
    because the three ceiling and bound answers assert different things about
    the speedup a template claimed.

    `INPUT_TOO_LARGE` asserts nothing: the naive solution finished at the largest
    storable input, and a separation may sit above it.
    `CASE_TOO_LARGE` proves it and carries the size, and only the case is lost.
    `NAIVE_FINISHED` is a defect in the run rather than in the problem, and
    `corpus.md` gives the three things that produce it.
    """

    NAIVE_FINISHED = "naive_finished"
    NAIVE_CRASHED = "naive_crashed"
    CANONICAL_FAILED = "canonical_failed"
    # every storable input the walk reached, the naive solution finished under the cap
    INPUT_TOO_LARGE = "input_too_large"
    # a separating size was found, and the case at it weighs too much
    CASE_TOO_LARGE = "case_too_large"
    DISAGREED = "disagreed"


@dataclass(frozen=True)
class Searched:
    """The separating case, or why there was none. The two are exclusive."""

    size: int | None = None
    case: SettledCase | None = None
    # what the child measured at that size. The naive solution's is absent where it
    # exceeded the measuring cap rather than merely the drill loop's
    canonical_ms: int | None = None
    naive_ms: int | None = None
    missing: Missing | None = None
    # the two solutions at that size, where they answered differently
    disagreement: Disagreement | None = None

    @property
    def found(self) -> bool:
        return self.missing is None

    @property
    def args(self) -> list[Any]:
        return self.case.args if self.case else []


def search(
    make: Callable[[int], Sequence[Any]],
    *,
    canonical: str,
    naive: str,
    reference: str,
    provenance: MachineProvenance,
    cap_ms: int,
    largest: int,
    smallest: int = 1,
    measure_ms: int = CAP_MS,
    ceiling: int = CEILING,
) -> Searched:
    """Double until the naive solution exceeds `cap_ms`, then halve to the
    smallest size that does. `largest` is what the statement's constraints
    allow: an input above it separates nothing, because no solution owes an
    answer there.
    """
    # measured well above the cap, so one run reads as a time rather than as a
    # timeout, and no later search re-runs what this one already measured
    if measure_ms <= cap_ms:
        raise ValueError("the measuring cap sits above the cap being separated")

    if smallest > largest:
        raise ValueError("the smallest size the search starts at is within the constraints")

    walk = _doubled(
        make, naive, smallest, largest, cap_ms=cap_ms, measure_ms=measure_ms, ceiling=ceiling
    )
    if isinstance(walk, Missing):
        return Searched(missing=walk)
    if walk.over is None and walk.capped and walk.fitted is not None:
        # the doubling leaves a factor of two under the ceiling untried, and a
        # quadratic naive solution separates in exactly that gap
        edge, args = _storable(make, walk.fitted, walk.size, ceiling)
        if edge > walk.fitted:
            exceeded, elapsed = _paces(naive, args, cap_ms=cap_ms, measure_ms=measure_ms)
            if exceeded is None:
                return Searched(missing=Missing.NAIVE_CRASHED)
            if exceeded:
                walk.over, walk.over_ms, walk.over_args = edge, elapsed, args

    if walk.over is None:
        return Searched(missing=Missing.INPUT_TOO_LARGE if walk.capped else Missing.NAIVE_FINISHED)
    under, over, over_ms, over_args = walk.under, walk.over, walk.over_ms, walk.over_args

    # runtime is taken to grow with the size: the halving needs it, and nothing
    # short of running every size in between would establish it
    while over - under > 1:
        middle = (under + over) // 2
        args = list(make(middle))
        exceeded, elapsed = _paces(naive, args, cap_ms=cap_ms, measure_ms=measure_ms)
        if exceeded is None:
            return Searched(missing=Missing.NAIVE_CRASHED)
        if exceeded:
            over, over_ms, over_args = middle, elapsed, args
        else:
            under = middle

    # the input that was measured rather than one built again: a generator is
    # asked to be deterministic, and the stored case is what the run decided
    return _settled(
        over_args,
        over,
        canonical=canonical,
        reference=reference,
        provenance=provenance,
        cap_ms=cap_ms,
        measure_ms=measure_ms,
        naive_ms=over_ms,
        ceiling=ceiling,
    )


@dataclass
class _Walk:
    """Where the doubling stopped: the last size the naive solution finished at, the
    first it exceeded the cap at, and whether the ceiling ended it first."""

    size: int
    under: int
    fitted: int | None = None
    over: int | None = None
    over_ms: int | None = None
    over_args: list[Any] = field(default_factory=list[Any])
    capped: bool = False


def _doubled(
    make: Callable[[int], Sequence[Any]],
    naive: str,
    smallest: int,
    largest: int,
    *,
    cap_ms: int,
    measure_ms: int,
    ceiling: int,
) -> _Walk | Missing:
    walk = _Walk(size=smallest, under=smallest)
    while True:
        args = list(make(walk.size))
        # stopped before the run rather than after it: an input over the
        # ceiling is one no case can carry, whatever the naive solution does on it
        if weighs(args) > ceiling:
            walk.capped = True
            return walk
        walk.fitted = walk.size
        exceeded, elapsed = _paces(naive, args, cap_ms=cap_ms, measure_ms=measure_ms)
        if exceeded is None:
            return Missing.NAIVE_CRASHED
        if exceeded:
            walk.over, walk.over_ms, walk.over_args = walk.size, elapsed, args
            return walk
        walk.under = walk.size
        if walk.size >= largest:
            return walk
        # clamped rather than doubled past it: the largest legal input is the
        # one size a search that found nothing has to have tried
        walk.size = min(walk.size * 2, largest)


def _storable(
    make: Callable[[int], Sequence[Any]], fits: int, over: int, ceiling: int
) -> tuple[int, list[Any]]:
    """The largest size under the ceiling, between one that fitted and one that
    did not. Costs builds alone: nothing is timed until the size is known."""
    args: list[Any] = []
    while over - fits > 1:
        middle = (fits + over) // 2
        built = list(make(middle))
        if weighs(built) > ceiling:
            over = middle
        else:
            fits, args = middle, built
    return fits, args


def _settled(
    args: list[Any],
    size: int,
    *,
    canonical: str,
    reference: str,
    provenance: MachineProvenance,
    cap_ms: int,
    measure_ms: int,
    naive_ms: int | None,
    ceiling: int,
) -> Searched:
    # the canonical is run under the cap it has to beat rather than the
    # measuring one: what the case asserts is that this solution answers there
    [ran] = run(canonical, [args], cap_ms=cap_ms)
    if not ran.returned:
        return Searched(missing=Missing.CANONICAL_FAILED)

    # carried onto every answer from here: the speedup is established at this
    # size whether or not a case is stored
    measured = partial(Searched, size=size, canonical_ms=ran.elapsed_ms, naive_ms=naive_ms)
    # the reference rather than the naive solution: what a case stores is the answer of
    # the solution written from the statement alone, whichever one was timed.
    # Settled as the first case set is, and by no round: the search runs after
    # the loop
    [theirs] = run(reference, [args], cap_ms=measure_ms)
    settled = settle(
        [args],
        canonical=[ran.value],
        reference=[answered(theirs)],
        provenance=provenance,
        round=None,
    )
    if not settled.agreed:
        return measured(missing=Missing.DISAGREED, disagreement=settled.disagreements[0])

    # the returned value weighs on the case as the arguments do
    (case,) = settled.cases
    if weighs(case.args) + weighs(case.expected) > ceiling:
        return measured(missing=Missing.CASE_TOO_LARGE)
    return measured(case=case)


def _paces(
    code: str,
    args: Sequence[Any],
    *,
    cap_ms: int,
    measure_ms: int,
) -> tuple[bool | None, int | None]:
    """Whether the naive solution exceeds `cap_ms` at this size and what it took. The
    first is `None` where it crashed, which is neither.

    Measured well above the cap, so a run a sitting would have cut short still
    reads as a time rather than as a timeout. What it answered is not read: the
    reference settles the case.
    """
    [ran] = run(code, [list(args)], cap_ms=measure_ms)
    if ran.outcome is RunOutcome.TIMEOUT:
        return True, None
    if not ran.returned:
        return None, None
    # measured whenever a value returned, so the fallback never decides
    return (ran.elapsed_ms or 0) > cap_ms, ran.elapsed_ms


__all__ = ["CEILING", "DRILL_CAP_MS", "Missing", "Searched", "search"]
