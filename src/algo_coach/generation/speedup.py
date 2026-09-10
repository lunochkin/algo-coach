"""The smallest input under which the naive solution exceeds the cap and the
canonical does not. Run only where the template claims a speedup.

Two solutions, two jobs: the naive one is the naive solution, and the reference
settles what the case at that size returns.
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

# the most a stored case may weigh, arguments and expected value together.
# `corpus.md` gives the reason and what a case over it costs
CEILING = 1_048_576

# the canonical finishes within a tenth of the cap at the separating point, so
# the case tests the form rather than the machine that ran it
MARGIN = 10

# the most calls a case may carry. Beyond it the module's own re-execution
# costs more than the calls, and the cap fires on the overhead
REPEATS_MAX = 100_000

# how many times the count step halves the input where the case it settled
# weighs too much. The walk fills the ceiling with arguments, and the answer is
# stored beside them
SHRINKS = 3

# bumped where the search's behaviour changes, so every held draft is searched
# again once. A draft records the three bounds above, and a change to the walk
# itself moves none of them. `flows.md` gives why this is a number a reader
# bumps rather than a hash of the code: the search is spread over four modules,
# and a hash of one would fire on a comment there and miss a change elsewhere
SEARCH_REVISION = 2


class Missing(StrEnum):
    """Why a search stored no separating case. Named rather than a boolean,
    because the three ceiling and bound answers assert different things about
    the speedup a template claimed.

    `COUNT_TOO_LARGE` asserts nothing: the naive solution finished at the
    largest storable input and the count that would reach the cap is out of
    bounds, so a separation may still sit above either.
    `CASE_TOO_LARGE` proves it and carries the size, and only the case is lost.
    `NAIVE_FINISHED` is a defect in the run rather than in the problem, and
    `corpus.md` gives the three things that produce it.
    """

    NAIVE_FINISHED = "naive_finished"
    NAIVE_CRASHED = "naive_crashed"
    CANONICAL_FAILED = "canonical_failed"
    # the canonical is over a tenth of the cap where the naive solution is over
    # the cap, so the two are within a constant factor and no count separates
    # them
    CANONICAL_TOO_SLOW = "canonical_too_slow"
    # every storable input the walk reached, the naive solution finished under
    # the cap. No search writes it since the count step ran after the walk, and
    # drafts written before that carry it
    INPUT_TOO_LARGE = "input_too_large"
    # the count that would reach the cap is over the bound, or one call is too
    # fast for the child's millisecond to divide the cap by
    COUNT_TOO_LARGE = "count_too_large"
    # a separating size was found, and the case at it weighs too much
    CASE_TOO_LARGE = "case_too_large"
    DISAGREED = "disagreed"


@dataclass(frozen=True)
class Searched:
    """The separating case, or why there was none. The two are exclusive."""

    size: int | None = None
    # how many calls the separating case carries, above one where the ceiling
    # ended the size walk with the naive solution still under the cap
    repeats: int = 1
    case: SettledCase | None = None
    # what the child measured at that size. The naive solution's is absent where
    # it exceeded the measuring cap rather than merely the drill loop's
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
        edged = _edged(walk, make, naive, cap_ms=cap_ms, measure_ms=measure_ms, ceiling=ceiling)
        if isinstance(edged, Missing):
            return Searched(missing=edged)
        walk = edged

    if walk.over is None:
        if not walk.capped:
            # the walk reached the statement's own bound, which `corpus.md`
            # names a defect in the run rather than a size the ceiling hid
            return Searched(missing=Missing.NAIVE_FINISHED)
        return _repeated(
            walk,
            make,
            canonical=canonical,
            naive=naive,
            reference=reference,
            provenance=provenance,
            cap_ms=cap_ms,
            measure_ms=measure_ms,
            ceiling=ceiling,
        )
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


def _repeated(
    walk: _Walk,
    make: Callable[[int], Sequence[Any]],
    *,
    canonical: str,
    naive: str,
    reference: str,
    provenance: MachineProvenance,
    cap_ms: int,
    measure_ms: int,
    ceiling: int,
) -> Searched:
    """The separating count, where the ceiling ended the size walk with the
    naive solution still under the cap.

    The walk fills the ceiling with arguments, so the answer stored beside them
    can carry the case over it. A smaller input costs more calls and nothing
    else, so the step halves and counts again.
    """
    size, args, per_call = walk.fitted, walk.fitted_args, walk.fitted_ms
    if size is None or not per_call:
        # nothing measurable to divide the cap by, so the calls are too fast to
        # count against a clock
        return Searched(missing=Missing.COUNT_TOO_LARGE)
    found = Searched(missing=Missing.COUNT_TOO_LARGE)
    for _ in range(SHRINKS):
        found = _counted(
            args,
            size,
            per_call,
            canonical=canonical,
            naive=naive,
            reference=reference,
            provenance=provenance,
            cap_ms=cap_ms,
            measure_ms=measure_ms,
            ceiling=ceiling,
        )
        if found.missing is not Missing.CASE_TOO_LARGE or size < 2:
            return found
        # the smaller input is not timed again: a call on half the input costs
        # about half as much, and the count step doubles from wherever it
        # starts. One millisecond is the child's resolution, so a second
        # measurement here reads zero and divides the cap by nothing
        size //= 2
        args = list(make(size))
    return found


def _counted(
    args: list[Any],
    size: int,
    per_call: int,
    *,
    canonical: str,
    naive: str,
    reference: str,
    provenance: MachineProvenance,
    cap_ms: int,
    measure_ms: int,
    ceiling: int,
) -> Searched:
    """The count at one size: the cap divided by one call, doubled while the
    confirmation falls short. Timing is noisy and the cost per call is not
    exactly flat, so the division alone is not taken for an answer."""
    count = -(-cap_ms // per_call)
    while count <= REPEATS_MAX:
        exceeded, elapsed = _paces(naive, args, cap_ms=cap_ms, measure_ms=measure_ms, repeats=count)
        if exceeded is None:
            return Searched(missing=Missing.NAIVE_CRASHED)
        if exceeded:
            return _settled(
                args,
                size,
                canonical=canonical,
                reference=reference,
                provenance=provenance,
                cap_ms=cap_ms,
                measure_ms=measure_ms,
                naive_ms=elapsed,
                ceiling=ceiling,
                repeats=count,
            )
        count *= 2
    return Searched(missing=Missing.COUNT_TOO_LARGE)


def _edged(
    walk: _Walk,
    make: Callable[[int], Sequence[Any]],
    naive: str,
    *,
    cap_ms: int,
    measure_ms: int,
    ceiling: int,
) -> _Walk | Missing:
    """The gap the doubling left under the ceiling. Doubling leaves a factor of
    two untried, and a quadratic naive solution separates in exactly that gap.

    A size that fits and does not exceed the cap is kept as the largest input
    measured, which is what the count step repeats.
    """
    assert walk.fitted is not None
    edge, args = _storable(make, walk.fitted, walk.size, ceiling)
    if edge <= walk.fitted:
        return walk
    exceeded, elapsed = _paces(naive, args, cap_ms=cap_ms, measure_ms=measure_ms)
    if exceeded is None:
        return Missing.NAIVE_CRASHED
    if exceeded:
        walk.over, walk.over_ms, walk.over_args = edge, elapsed, args
    else:
        walk.fitted, walk.fitted_ms, walk.fitted_args = edge, elapsed, args
    return walk


@dataclass
class _Walk:
    """Where the doubling stopped: the last size the naive solution finished at,
    the first it exceeded the cap at, and whether the ceiling ended it first."""

    size: int
    under: int
    fitted: int | None = None
    # the largest storable input the naive solution finished on, and what it
    # took there: the count step measures its calls against that time
    fitted_ms: int | None = None
    fitted_args: list[Any] = field(default_factory=list[Any])
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
        # stopped before the run rather than after it: an input over the ceiling
        # is one no case can carry, whatever the naive solution does on it
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
        walk.fitted_ms, walk.fitted_args = elapsed, args
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
    repeats: int = 1,
) -> Searched:
    # the canonical is run under the cap it has to beat rather than the
    # measuring one: what the case asserts is that this solution answers there
    [ran] = run(canonical, [args], cap_ms=cap_ms, repeats=[repeats])
    if not ran.returned:
        return Searched(missing=Missing.CANONICAL_FAILED)

    # carried onto every answer from here: the speedup is established at this
    # size whether or not a case is stored
    measured = partial(
        Searched, size=size, repeats=repeats, canonical_ms=ran.elapsed_ms, naive_ms=naive_ms
    )
    # a case the canonical only just answers fails a correct submission that is
    # a few percent slower, so the margin is what makes it a test of the form
    if (ran.elapsed_ms or 0) * MARGIN > cap_ms:
        return measured(missing=Missing.CANONICAL_TOO_SLOW)
    # the reference rather than the naive solution: what a case stores is the
    # answer of the solution written from the statement alone, whichever one was
    # timed. Settled as the first case set is, and by no round: the search runs
    # after the loop
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
    return measured(case=case.model_copy(update={"repeats": repeats}))


def _paces(
    code: str,
    args: Sequence[Any],
    *,
    cap_ms: int,
    measure_ms: int,
    repeats: int = 1,
) -> tuple[bool | None, int | None]:
    """Whether the naive solution exceeds `cap_ms` at this size and what it
    took. The first is `None` where it crashed, which is neither.

    Measured well above the cap, so a run a sitting would have cut short still
    reads as a time rather than as a timeout. What it answered is not read: the
    reference settles the case.
    """
    [ran] = run(code, [list(args)], cap_ms=measure_ms, repeats=[repeats])
    if ran.outcome is RunOutcome.TIMEOUT:
        return True, None
    if not ran.returned:
        return None, None
    # measured whenever a value returned, so the fallback never decides
    return (ran.elapsed_ms or 0) > cap_ms, ran.elapsed_ms


__all__ = ["CEILING", "Missing", "Searched", "search"]
