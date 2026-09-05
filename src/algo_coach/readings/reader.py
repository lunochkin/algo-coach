"""Reading one solution for its techniques, and storing what came back."""

from collections.abc import Sequence

from algo_coach.calls import CallLog, Configuration, Transport
from algo_coach.classifier import DEFAULT, classify
from algo_coach.mint import machine_reading
from algo_coach.readings.store import ReadingLog
from algo_coach.schema import Call, MachineProvenance, Solution, TechniqueReading
from algo_coach.techniques import codes


def candidates() -> list[str]:
    # sorted: the order reaches the prompt the digest is taken over, and a
    # frozenset's own order moves with the interpreter's hash seed.
    return sorted(codes())


def read_one(
    transport: Transport,
    calls: CallLog,
    solution: Solution,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """What one classifier reads one solution as, and the call that read it.

    Writes no reading, so several may run at once.
    """
    return classify(transport, calls, candidates(), solution.code, configuration=configuration)


def store(
    log: ReadingLog,
    solution_id: str,
    techniques: Sequence[str],
    call: Call,
) -> TechniqueReading:
    """Append what a classifier read, on the calling thread."""
    reading = machine_reading(solution_id, list(techniques), written=MachineProvenance.of(call))
    log.append(reading)
    return reading


def read(
    transport: Transport,
    log: ReadingLog,
    calls: CallLog,
    solution: Solution,
    *,
    configuration: Configuration = DEFAULT,
) -> list[str]:
    """Read one solution and store the verdict, returning what was named."""
    techniques, call = read_one(transport, calls, solution, configuration=configuration)
    # No call means fewer than two candidates were offered, which the whole
    # vocabulary never is; a reading with no configuration cannot be stored.
    if call is not None:
        store(log, solution.id, techniques, call)
    return techniques
