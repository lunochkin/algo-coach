"""Reading one solution for its techniques, and storing what came back.

The reader is `algo_coach.classifier`, shared with the attempt classifier: one
prompt, one transport and one staleness rule, so the two records stay
comparable. What is here is the half that differs — the record written is a
`TechniqueReading` about code the engine wrote, not a `TechniqueClaim` about a
sitting.
"""

from collections.abc import Sequence

from algo_coach.calls import CallLog, Transport
from algo_coach.classifier import DEFAULT, Configuration, classify
from algo_coach.mint import machine_reading
from algo_coach.readings.store import ReadingLog
from algo_coach.schema import Call, Solution, TechniqueReading


def read_one(
    transport: Transport,
    calls: CallLog,
    solution: Solution,
    candidates: Sequence[str],
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """What one classifier reads one solution as, and the call that read it.

    Makes the call and writes no reading, so it is safe to run several at once.
    The record is the caller's, and the reading log has one writer however many
    calls are in flight.

    The candidates are the caller's too. An attempt is read against its
    problem's own techniques; a solution is read against the whole vocabulary,
    since those techniques are folded from these readings and constraining one
    by them would be circular.
    """
    return classify(transport, calls, candidates, solution.code, configuration=configuration)


def store(
    log: ReadingLog,
    solution_id: str,
    techniques: Sequence[str],
    call: Call,
) -> TechniqueReading:
    """Append what a classifier read, on the calling thread.

    Only ever after a call, as a claim is. The configuration and the digest are
    copied from the call so the reading log reads without opening the call log,
    and the call is cited for what only it holds: the tokens, the response, the
    reasoning.
    """
    reading = machine_reading(
        solution_id,
        list(techniques),
        model=call.model,
        effort=call.effort,
        prompt_hash=call.prompt_hash,
        call_id=call.id,
        pin=call.pin or "",
        temperature=call.temperature,
        provider=call.provider,
        cost=call.cost,
    )
    log.append(reading)
    return reading


def read(
    transport: Transport,
    log: ReadingLog,
    calls: CallLog,
    solution: Solution,
    candidates: Sequence[str],
    *,
    configuration: Configuration = DEFAULT,
) -> list[str]:
    """Read one solution and store the verdict, returning what was named.

    An empty verdict is stored, where an empty claim leaves the attempt to the
    fallback. Nothing falls back here — a problem's techniques are folded from
    these readings — so naming none of the vocabulary is this reader's answer
    about the code, and unstored it would be paid for again.

    Nothing is stored where no call was made. A reading carries its whole
    configuration, so a verdict nobody read cannot be written down; the
    candidate set that short-circuits the reader is the whole vocabulary here,
    so a corpus run never reaches it. Failures are the caller's, as they are
    for a claim.
    """
    techniques, call = read_one(transport, calls, solution, candidates, configuration=configuration)
    if call is not None:
        store(log, solution.id, techniques, call)
    return techniques
