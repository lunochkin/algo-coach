"""Reading one solution for its techniques, and storing what came back."""

from collections.abc import Sequence

from algo_coach.calls import CallLog, Transport
from algo_coach.classifier import DEFAULT, classify
from algo_coach.mint import machine_solution_claim
from algo_coach.schema import Call, Configuration, MachineProvenance, Solution, SolutionClaim
from algo_coach.solution_claims.store import SolutionClaimLog
from algo_coach.techniques import codes


def candidates() -> list[str]:
    # sorted: the order reaches the prompt, so the prompt hash is taken over it,
    # and a frozenset's own order moves with the interpreter's hash seed.
    return sorted(codes())


def read_one(
    transport: Transport,
    calls: CallLog,
    solution: Solution,
    *,
    configuration: Configuration = DEFAULT,
) -> tuple[list[str], Call | None]:
    """What one classifier reads one solution as, and the call that read it.

    Writes no claim, so several may run at once.
    """
    return classify(transport, calls, candidates(), solution.code, configuration=configuration)


def store(
    log: SolutionClaimLog,
    solution_id: str,
    techniques: Sequence[str],
    call: Call,
) -> SolutionClaim:
    """Append what a classifier read, on the calling thread."""
    claim = machine_solution_claim(
        solution_id, list(techniques), provenance=MachineProvenance.of(call)
    )
    log.append(claim)
    return claim


def read(
    transport: Transport,
    log: SolutionClaimLog,
    calls: CallLog,
    solution: Solution,
    *,
    configuration: Configuration = DEFAULT,
) -> list[str]:
    """Read one solution and store the verdict, returning what was named."""
    techniques, call = read_one(transport, calls, solution, configuration=configuration)
    # the whole vocabulary is never fewer than two candidates, so the call was
    # made; a claim with no configuration could not be stored
    assert call is not None
    store(log, solution.id, techniques, call)
    return techniques
