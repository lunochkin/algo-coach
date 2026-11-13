"""The two answering steps whose failure costs a site rather than the problem:
the input generator and the naive solution."""

from algo_coach.calls import CallLog, Transport
from algo_coach.generation.aim import Target
from algo_coach.generation.checks import wrong_on
from algo_coach.generation.inputs import write_input_generator
from algo_coach.generation.naive import write_naive
from algo_coach.generation.steps import SILENT, Notes
from algo_coach.generation.verdicts import Inputs, Naive
from algo_coach.schema import Configuration, Draft, MachineProvenance


def building(
    transport: Transport,
    calls: CallLog,
    statement: str,
    *,
    configuration: Configuration,
    notes: Notes = SILENT,
) -> Inputs:
    """The code that builds an input of a given size, for every problem.

    A call that fails costs the inputs rather than the problem: it says nothing
    about the statement, as a failed search does not.
    """
    notes("inputs", "writing the input generator")
    try:
        generator, call = write_input_generator(
            transport, calls, statement, configuration=configuration
        )
    except Exception as failure:
        notes("inputs", f"unbuilt: {failure!r}")
        return Inputs(unbuilt=repr(failure))
    notes("inputs", f"written, up to {generator.largest}", call)
    return Inputs(call=call, input_generator=generator, provenance=MachineProvenance.of(call))


def paced(
    transport: Transport,
    calls: CallLog,
    draft: Draft,
    target: Target,
    *,
    configuration: Configuration,
    cap_ms: int,
    notes: Notes = SILENT,
    reuse: bool = True,
) -> Naive:
    """The naive solution, or the one the draft already holds, run against the
    set the two solutions settled.

    A call that fails costs the naive solution rather than the problem, as a
    failed input generator does. So does one whose answer is wrong: what it says
    is that this solution measures nothing, not that the statement is unsound.
    """
    if reuse and draft.naive is not None:
        notes("naive", "reused, at the configuration that wrote it")
        naive = Naive(code=draft.naive, provenance=draft.naive_provenance)
    else:
        notes("naive", "writing the solution the search measures against")
        try:
            code, call = write_naive(
                transport, calls, draft.statement, target, configuration=configuration
            )
        except Exception as failure:
            notes("naive", f"unpaced: {failure!r}")
            return Naive(unpaced=repr(failure))
        notes("naive", "written", call)
        naive = Naive(call=call, code=code, provenance=MachineProvenance.of(call))

    # run again on a reuse: the draft stores the code rather than the verdict,
    # and a subprocess answers this for nothing
    detail = wrong_on(draft.cases, code=naive.code or "", cap_ms=cap_ms)
    if detail is None:
        return naive
    notes("naive", detail)
    # the call is kept, since the site answered and the record is what says
    # what it cost. Nothing is stored, so the draft stops at the step before
    return naive.model_copy(update={"code": None, "unpaced": detail})


__all__ = ["building", "paced"]
