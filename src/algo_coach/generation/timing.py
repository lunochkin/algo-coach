"""The speedup search over the builder's inputs, and what it leaves on the
inputs site. `corpus.md` gives what a separating size means."""

from collections.abc import Callable
from typing import Any

from algo_coach.generation.checks import (
    Checked,
    Discard,
)
from algo_coach.generation.errors import GenerationError
from algo_coach.generation.inputs import Built
from algo_coach.generation.speedup import DRILL_CAP_MS, Missing, Searched, search
from algo_coach.generation.steps import SILENT, Notes
from algo_coach.generation.verdicts import Clock, Inputs
from algo_coach.runner import NoValue, outputs
from algo_coach.schema import (
    Draft,
    MachineProvenance,
    SettledCase,
    Template,
)

# the seed the speedup search builds at, which never varies: the halving
# compares one size against another, so two inputs of one shape are needed
SEARCH_SEED = 0


def make(code: str, cap_ms: int, *, seed: int = SEARCH_SEED) -> Callable[[int], list[Any]]:
    """The generator behind the callable the search takes: run through the
    executor as any other code, so nothing model-written runs in this process.

    One seed throughout, or the halving would compare two different inputs.
    """

    def built(size: int) -> list[Any]:
        [args] = outputs(code, [[size, seed]], cap_ms=cap_ms)
        if isinstance(args, NoValue) or not isinstance(args, list):
            raise GenerationError(f"the input generator built nothing at size {size}")
        return args

    return built


def separated(
    built: Built,
    *,
    canonical: str,
    naive: str,
    reference: str,
    written: MachineProvenance,
    cap_ms: int,
) -> Searched:
    """The search over the builder's inputs. The generation cap measures, and
    the sitting's cap is what a size is separated against."""
    return search(
        make(built.code, cap_ms),
        canonical=canonical,
        naive=naive,
        reference=reference,
        written=written,
        cap_ms=DRILL_CAP_MS,
        largest=built.largest,
        measure_ms=cap_ms,
    )


def found_in(inputs: Inputs, found: Searched) -> Inputs:
    """What the search left on the inputs site. `separating` is carried where
    the search proved a separation and stored nothing, which `unseparated`
    beside it is what tells apart from a stored one."""
    return inputs.model_copy(
        update={
            "separating": found.size,
            "unseparated": found.missing,
            "gate": Discard.DISAGREED if found.missing is Missing.DISAGREED else None,
        }
    )


def searched_note(found: Searched) -> str:
    return f"separates at {found.size}" if found.found else f"no case: {found.missing}"


def timed(
    template: Template,
    draft: Draft,
    checked: Checked,
    inputs: Inputs,
    clock: Clock,
    *,
    cap_ms: int,
    notes: Notes = SILENT,
) -> tuple[Checked, Inputs, SettledCase | None]:
    """The timing case, returned rather than appended: the caller holds it back
    until the mutation loop has run.

    A search that fails costs the case rather than the problem, so its failure
    is caught here instead of reaching the run's abort count.
    """
    if not template.speedup or inputs.built is None or inputs.written is None:
        return checked, inputs, None
    if clock.code is None:
        raise ValueError("the search measures the canonical against a naive solution")
    notes("timing", "searching for the input that separates the two solutions")
    try:
        found = separated(
            inputs.built,
            canonical=draft.canonical,
            naive=clock.code,
            reference=draft.reference or "",
            written=inputs.written,
            cap_ms=cap_ms,
        )
    except Exception as failure:
        notes("timing", f"unsearched: {failure!r}")
        return checked, inputs.model_copy(update={"unseparated": repr(failure)}), None

    notes("timing", searched_note(found))
    searched = found_in(inputs, found)
    if found.found:
        return checked, searched, found.case
    if found.missing is not Missing.DISAGREED:
        return checked, searched, None
    # one input the small cases could not reach, answered two ways
    discarded = Checked(
        outcome=checked.outcome,
        discard=Discard.DISAGREED,
        disagreements=[found.disagreement] if found.disagreement is not None else [],
    )
    return discarded, searched, None


__all__ = [
    "SEARCH_SEED",
    "found_in",
    "make",
    "searched_note",
    "separated",
    "timed",
]
