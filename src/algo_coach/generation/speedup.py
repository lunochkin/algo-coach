"""The smallest input under which the naive solution exceeds the cap and the
canonical does not. Run only where the template claims a speedup.

Two solutions, two jobs: the naive one is the clock, and the reference settles
what the case at that size returns.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from algo_coach.generation.agreement import Disagreement, SettledCase
from algo_coach.generation.checks import CAP_MS
from algo_coach.runner import RunOutcome, agrees, as_json, run
from algo_coach.schema import ExpectedSource, MachineProvenance

# the cap a sitting judges a submission under, which is what the separating
# case is chosen against. Phase 8 reads it; generation's own cap sits above it
DRILL_CAP_MS = 2_000

# the most a stored case may weigh, arguments and expected value together.
# `corpus.md` gives the reason and what a case over it costs
CEILING = 65_536


class Missing(StrEnum):
    """Why a search stored no separating case. Named rather than a boolean,
    because the three ceiling and bound answers assert different things about
    the speedup a template claimed.

    `INPUT_TOO_LARGE` asserts nothing: the walk stopped before it could look.
    `CASE_TOO_LARGE` proves it and carries the size, and only the case is lost.
    `NAIVE_FINISHED` is a defect in the run rather than in the problem, and
    `corpus.md` gives the three things that produce it.
    """

    NAIVE_FINISHED = "naive_finished"
    NAIVE_CRASHED = "naive_crashed"
    CANONICAL_FAILED = "canonical_failed"
    # the built input crossed the ceiling before the clock exceeded the cap
    INPUT_TOO_LARGE = "input_too_large"
    # a separating size was found, and the case at it weighs too much
    CASE_TOO_LARGE = "case_too_large"
    DISAGREED = "disagreed"


@dataclass(frozen=True)
class Searched:
    """The separating case, or why there was none. The two are exclusive."""

    size: int | None = None
    case: SettledCase | None = None
    # what the child measured at that size. The clock's is absent where it
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
    written: MachineProvenance,
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

    under, over, over_ms, over_args, capped = smallest, None, None, [], False
    size = smallest
    while True:
        args = list(make(size))
        # stopped before the run rather than after it: an input over the
        # ceiling is one no case can carry, whatever the clock does on it
        if _weighs(args) > ceiling:
            capped = True
            break
        exceeded, elapsed = _paces(naive, args, cap_ms=cap_ms, measure_ms=measure_ms)
        if exceeded is None:
            return Searched(missing=Missing.NAIVE_CRASHED)
        if exceeded:
            over, over_ms, over_args = size, elapsed, args
            break
        under = size
        if size >= largest:
            break
        # clamped rather than doubled past it: the largest legal input is the
        # one size a search that found nothing has to have tried
        size = min(size * 2, largest)

    if over is None:
        return Searched(missing=Missing.INPUT_TOO_LARGE if capped else Missing.NAIVE_FINISHED)

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
        written=written,
        cap_ms=cap_ms,
        measure_ms=measure_ms,
        naive_ms=over_ms,
        ceiling=ceiling,
    )


def _settled(
    args: list[Any],
    size: int,
    *,
    canonical: str,
    reference: str,
    written: MachineProvenance,
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

    measured = {"size": size, "canonical_ms": ran.elapsed_ms, "naive_ms": naive_ms}
    # the reference rather than the clock: what a case stores is the answer of
    # the solution written from the statement alone, whichever one was timed
    [theirs] = run(reference, [args], cap_ms=measure_ms)
    # the settle rule the first case set uses: the reference's answer wherever
    # it computed one, and the canonical's only beyond its reach
    if not theirs.returned:
        expected, source = ran.value, ExpectedSource.CANONICAL
    elif agrees(ran.value, theirs.value):
        expected, source = theirs.value, ExpectedSource.REFERENCE
    else:
        return Searched(
            missing=Missing.DISAGREED,
            disagreement=Disagreement(args=args, canonical=ran.value, reference=theirs.value),
            **measured,
        )

    # the returned value weighs on the case as the arguments do. `measured` is
    # carried: the speedup is established at this size, and only the case is
    # not
    if _weighs(args) + _weighs(expected) > ceiling:
        return Searched(missing=Missing.CASE_TOO_LARGE, **measured)
    return Searched(
        # no round won it: the search runs after the loop
        case=SettledCase(
            args=args,
            expected=expected,
            expected_from=source,
            written=written,
            round=None,
        ),
        **measured,
    )


def _weighs(value: Any) -> int:
    return len(as_json(value).encode())


def _paces(
    code: str,
    args: Sequence[Any],
    *,
    cap_ms: int,
    measure_ms: int,
) -> tuple[bool | None, int | None]:
    """Whether the clock exceeds `cap_ms` at this size and what it took. The
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
    return ran.elapsed_ms > cap_ms, ran.elapsed_ms


__all__ = ["CEILING", "DRILL_CAP_MS", "Missing", "Searched", "search"]
