"""What each answering site leaves on one attempt, and how a site outcome
reads it. `machine.md` gives what the records carry."""

from typing import TypedDict

from pydantic import BaseModel

from algo_coach.generation.checks import (
    Checked,
    Gate,
)
from algo_coach.generation.hardening import Hardened
from algo_coach.generation.inputs import InputGenerator
from algo_coach.schema import (
    Call,
    MachineProvenance,
)


class Inputs(BaseModel):
    """What the inputs site left: the code it wrote to build an input, and what
    the speedup search made of that code.

    The generator is written for every problem, so `built` stands where the
    search never ran. Both search fields are absent where the form is its own
    optimum and nothing was looked for.
    """

    call: Call | None = None
    input_generator: InputGenerator | None = None
    # the configuration the code was written at, which is what the cases it
    # feeds carry. A resume past this step reuses it where there is no call
    provenance: MachineProvenance | None = None
    unbuilt: str | None = None  # the call failed, and no code was written
    separating: int | None = None  # the size the naive solution stops fitting at
    unseparated: str | None = None  # why there was none, where one was looked for
    gate: Gate | None = None  # the two solutions disagreed at that size


class Naive(BaseModel):
    """What the naive site left: the naive solution the search measures the
    canonical against, or why there is none.

    Empty where the template claims no speedup, as the search's own fields are.
    """

    call: Call | None = None
    code: str | None = None
    # the configuration the solution was written at. A resume past this step
    # reuses it where there is no call
    provenance: MachineProvenance | None = None
    unpaced: str | None = None  # the call failed, and no naive solution was written


class Bar(BaseModel):
    """What the mutation loop reported. `unmeasured` is a call that failed,
    which costs the round rather than the problem."""

    mutants: int = 0
    survived: int = 0
    won: int = 0  # cases the rounds appended to the set
    proposed: int = 0  # what they proposed to it, so the difference killed nothing
    # the fuzz pass before them: the inputs it built and the ones it kept,
    # which cost subprocesses rather than a call
    built: int = 0
    kept: int = 0
    # which source killed what, each written on the site whose output did it
    declared: int = 0
    fuzzed: int = 0
    rounds: list[int] = []
    # the last round's call, which is what the counters were left by. Absent
    # where nothing reached a round
    call: Call | None = None
    # a round's proposal the two solutions answered differently. The fuzz
    # pass's own is the inputs site's, since its code built the input
    gate: Gate | None = None
    unmeasured: str | None = None


class GateVerdict(TypedDict, total=False):
    """What a site's record carries where its answer met a gate."""

    gate: Gate | None
    detail: str


class LoopVerdict(TypedDict):
    """What the discrimination site's record carries."""

    gate: Gate | None
    survived: int
    won: int
    proposed: int
    killed: int
    rounds: list[int]


class SearchVerdict(TypedDict):
    """What the inputs site's record carries of the search that judged it."""

    gate: Gate | None
    separating: int | None
    unseparated: str | None
    largest: int | None


def gated(checked: Checked, *gates: Gate) -> GateVerdict:
    """The gate this site's answer was rejected by, and what it said. A reject
    belongs to the site whose output made it decidable."""
    if checked.gate not in gates:
        return GateVerdict()
    return GateVerdict(gate=checked.gate, detail=reason(checked))


def settled(checked: Checked) -> str:
    """What the two runs left, as the stage line reports it."""
    if not checked.survived:
        return why(checked)
    counted = f"{checked.outcome}, {len(checked.cases)} case(s) settled"
    if not checked.misdeclarations:
        return counted
    return f"{counted}, {len(checked.misdeclarations)} misdeclared"


def reason(checked: Checked) -> str:
    """What the gate said, as a site outcome's detail carries it. A count
    rather than the cases: the failing arguments are on the `Checked`."""
    match checked.gate:
        case Gate.NO_VALUE:
            return f"the canonical {checked.outcome} on some case"
        case Gate.UNTESTED:
            return "the reference computed no case"
        case _:
            return f"the two solutions disagree on {len(checked.disagreements)} case(s)"


def why(checked: Checked) -> str:
    return f"rejected: {reason(checked)}"


def blind_verdicts(checked: Checked) -> GateVerdict:
    """What the blind site's record carries: the gate its reading was rejected
    by, where one was."""
    return gated(checked, Gate.UNTESTED, Gate.DISAGREED)


def loop_verdicts(bar: Bar) -> LoopVerdict:
    """What the discrimination site's record carries. The mutants are not among
    them: they sit on the site that wrote the canonical."""
    return LoopVerdict(
        gate=bar.gate,
        survived=bar.survived,
        won=bar.won,
        proposed=bar.proposed,
        killed=sum(bar.rounds),
        rounds=bar.rounds,
    )


def search_verdicts(inputs: Inputs) -> SearchVerdict:
    """What the inputs site's record carries of the search that judged it. The
    bound is kept here, since a landed problem clears the draft that held it."""
    return SearchVerdict(
        gate=inputs.gate,
        separating=inputs.separating,
        unseparated=inputs.unseparated,
        largest=inputs.input_generator.largest if inputs.input_generator is not None else None,
    )


def barred(hardened: Hardened) -> Bar:
    """What the loop left, as the discrimination site's record counts it."""
    return Bar(
        mutants=hardened.mutants,
        survived=hardened.survived,
        won=len(hardened.won),
        proposed=hardened.proposed,
        built=hardened.fuzzed.built if hardened.fuzzed else 0,
        kept=len(hardened.kept),
        declared=hardened.declared,
        fuzzed=hardened.fuzzed.killed if hardened.fuzzed else 0,
        rounds=hardened.rounds,
        call=hardened.call,
    )


__all__ = [
    "Bar",
    "GateVerdict",
    "Inputs",
    "LoopVerdict",
    "Naive",
    "SearchVerdict",
    "barred",
    "blind_verdicts",
    "gated",
    "loop_verdicts",
    "reason",
    "search_verdicts",
    "settled",
    "why",
]
