"""The smallest input under which the reference exceeds the cap and the
canonical does not. Run only where the template claims a speedup."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from algo_coach.generation.agreement import Disagreement, SettledCase
from algo_coach.generation.checks import CAP_MS
from algo_coach.runner import RunOutcome, agrees, as_json, run
from algo_coach.schema import Call, ExpectedSource

# the cap a sitting judges a submission under, which is what the separating
# case is chosen against. Phase 8 reads it; generation's own cap sits above it
DRILL_CAP_MS = 2_000

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
    DISAGREED = "disagreed"


@dataclass(frozen=True)
class Searched:
    """The separating case, or why there was none. The two are exclusive."""

    size: int | None = None
    case: SettledCase | None = None
    # what the child measured at that size. The reference's is absent where it
    # exceeded the measuring cap rather than merely the drill loop's
    canonical_ms: int | None = None
    reference_ms: int | None = None
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
    reference: str,
    call: Call,
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

    under, over, over_ms, over_args, over_value, capped = smallest, None, None, [], None, False
    size = smallest
    while True:
        args = list(make(size))
        # stopped before the run rather than after it: an input over the
        # ceiling is one no case can carry, whatever the reference does on it
        if _weighs(args) > ceiling:
            capped = True
            break
        exceeded, elapsed, value = _reference(reference, args, cap_ms=cap_ms, measure_ms=measure_ms)
        if exceeded is None:
            return Searched(missing=Missing.REFERENCE_CRASHED)
        if exceeded:
            over, over_ms, over_args, over_value = size, elapsed, args, value
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
        args = list(make(middle))
        exceeded, elapsed, value = _reference(reference, args, cap_ms=cap_ms, measure_ms=measure_ms)
        if exceeded is None:
            return Searched(missing=Missing.REFERENCE_CRASHED)
        if exceeded:
            over, over_ms, over_args, over_value = middle, elapsed, args, value
        else:
            under = middle

    # the input that was measured rather than one built again: a generator is
    # asked to be deterministic, and the stored case is what the run decided
    return _settled(
        over_args,
        over,
        canonical=canonical,
        call=call,
        cap_ms=cap_ms,
        reference_ms=over_ms,
        reference_value=over_value,
        ceiling=ceiling,
    )


def _settled(
    args: list[Any],
    size: int,
    *,
    canonical: str,
    call: Call,
    cap_ms: int,
    reference_ms: int | None,
    reference_value: Any,
    ceiling: int,
) -> Searched:
    # the canonical is run under the cap it has to beat rather than the
    # measuring one: what the case asserts is that this solution answers there
    [ran] = run(canonical, [args], cap_ms=cap_ms)
    if not ran.returned:
        return Searched(missing=Missing.CANONICAL_FAILED)

    measured = {"size": size, "canonical_ms": ran.elapsed_ms, "reference_ms": reference_ms}
    # the settle rule the first case set uses: the reference's answer wherever
    # it computed one, and the canonical's only beyond its reach
    if reference_ms is None:
        expected, source = ran.value, ExpectedSource.CANONICAL
    elif agrees(ran.value, reference_value):
        expected, source = reference_value, ExpectedSource.REFERENCE
    else:
        return Searched(
            missing=Missing.DISAGREED,
            disagreement=Disagreement(args=args, canonical=ran.value, reference=reference_value),
            **measured,
        )

    # the returned value weighs on the case as the arguments do
    if _weighs(args) + _weighs(expected) > ceiling:
        return Searched(missing=Missing.INPUT_TOO_LARGE)
    return Searched(
        # no round won it: the search runs after the loop
        case=SettledCase(args=args, expected=expected, expected_from=source, call=call, round=None),
        **measured,
    )


def _weighs(value: Any) -> int:
    return len(as_json(value).encode())


def _reference(
    code: str,
    args: Sequence[Any],
    *,
    cap_ms: int,
    measure_ms: int,
) -> tuple[bool | None, int | None, Any]:
    """Whether the reference exceeds `cap_ms` at this size, what it took, and
    what it answered. The first is `None` where it crashed, which is neither.

    Measured well above the cap, so a run that a sitting would have cut short
    still returns a value, and the case it becomes is not the canonical's own.
    """
    [ran] = run(code, [list(args)], cap_ms=measure_ms)
    if ran.outcome is RunOutcome.TIMEOUT:
        return True, None, None
    if not ran.returned:
        return None, None, None
    return ran.elapsed_ms > cap_ms, ran.elapsed_ms, ran.value


__all__ = ["CEILING", "DRILL_CAP_MS", "Missing", "Searched", "search"]
