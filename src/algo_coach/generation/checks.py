"""Running the two solutions, and whether what they answered lets the problem
land.

Two steps rather than one, in the order `flows.md` gives: the canonical is run
and read against what its own call declared, and only then is it settled
against a reference. The reading rejects nothing, since one call wrote both.

Stores nothing: the ids a case and a solution need do not exist until it lands.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from algo_coach.generation.agreement import (
    Disagreement,
    Misdeclaration,
    misdeclared,
    settle,
)
from algo_coach.mutation import Case
from algo_coach.runner import NoValue, agrees, answered, decide, outputs, run
from algo_coach.schema import (
    CaseOutcome,
    DraftCase,
    Gate,
    MachineProvenance,
    SettledCase,
    severest,
)

# the per-case cap at generation, well above the drill loop's: what the
# reference has to finish under
CAP_MS = 10_000


@dataclass(frozen=True)
class Ran:
    """The canonical's own run, before any reference exists. `returned` is what
    it answered, kept so the settling does not run it a second time."""

    outcome: CaseOutcome | None
    slowest_ms: int | None = None
    returned: list[Any] = field(default_factory=list[Any])
    gate: Gate | None = None
    misdeclarations: list[Misdeclaration] = field(default_factory=list[Misdeclaration])

    @property
    def survived(self) -> bool:
        return self.gate is None


@dataclass(frozen=True)
class Checked:
    """What the two runs decided about one drafted problem. `cases` is empty
    where it was rejected."""

    # how the canonical's run went, folded to the severest case. `None` only
    # where there were no cases to run
    outcome: CaseOutcome | None
    # what the canonical's slowest case took in that run. The mutation loop
    # paces its cap by it rather than running the canonical again
    slowest_ms: int | None = None
    gate: Gate | None = None
    cases: list[SettledCase] = field(default_factory=list[SettledCase])
    misdeclarations: list[Misdeclaration] = field(default_factory=list[Misdeclaration])
    disagreements: list[Disagreement] = field(default_factory=list[Disagreement])

    @property
    def survived(self) -> bool:
        return self.gate is None


def mistakes[C: Case](cases: Sequence[C], *, code: str, cap_ms: int = CAP_MS) -> list[C]:
    """The cases a solution answered and got wrong.

    A case it did not finish is not among them: being slow is what the naive
    solution is for, and only a computed answer can be wrong.
    """
    ran = outputs(code, [case.args for case in cases], cap_ms=cap_ms)
    return [
        case
        for case, value in zip(cases, ran, strict=True)
        if not isinstance(value, NoValue) and not agrees(value, case.expected)
    ]


def wrong_on(cases: Sequence[Case], *, code: str, cap_ms: int = CAP_MS) -> str | None:
    """The naive solution's verdict as its record carries it, or nothing where
    every case it answered was right."""
    wrong = mistakes(cases, code=code, cap_ms=cap_ms)
    return f"wrong on {len(wrong)} case(s)" if wrong else None


def check(cases: Sequence[DraftCase], *, canonical: str, cap_ms: int = CAP_MS) -> Ran:
    """The canonical alone, before a blind call is paid for. A case it answered
    differently from its own call's `expected` is counted rather than gated:
    one call wrote the code and the declaration, so they share a reading."""
    args = [case.args for case in cases]
    ran = run(canonical, args, cap_ms=cap_ms)
    ours = [answered(one) for one in ran]
    # folded over how the run went rather than over the declared values: a case
    # answered differently from the declaration is counted, and the reference
    # is what decides whether the answer is wrong
    outcome = severest(decide(one, one.value) for one in ran)
    slowest = max((one.elapsed_ms or 0 for one in ran if one.returned), default=0)

    if any(isinstance(one, NoValue) for one in ours):
        return Ran(outcome=outcome, slowest_ms=slowest, gate=Gate.NO_VALUE)

    return Ran(
        outcome=outcome,
        slowest_ms=slowest,
        returned=ours,
        misdeclarations=misdeclared(cases, ours),
    )


def stopped(ran: Ran) -> Checked:
    """The canonical's own verdict, where it is the run's. Only `no_value` can
    reach here, so nothing was settled and no reference disagreed."""
    return Checked(
        outcome=ran.outcome,
        slowest_ms=ran.slowest_ms,
        gate=ran.gate,
        misdeclarations=ran.misdeclarations,
    )


def agree(
    ran: Ran,
    cases: Sequence[Case],
    *,
    reference: str,
    provenance: MachineProvenance,
    cap_ms: int = CAP_MS,
) -> Checked:
    """The reference against the canonical's answers, which is what settles a
    case. The canonical is not run again: `ran` carries what it returned.

    `written` is the generator's configuration rather than the blind call's:
    the arguments are the statement's own cases, whoever computed what they
    return."""
    args = [case.args for case in cases]
    theirs = outputs(reference, args, cap_ms=cap_ms)
    settled = settle(args, canonical=ran.returned, reference=theirs, provenance=provenance)

    # carried rather than dropped at the gate it no longer is: the count is
    # what the generator's own record is scored on
    def checked(
        *,
        gate: Gate | None = None,
        cases: list[SettledCase] | None = None,
        disagreements: list[Disagreement] | None = None,
    ) -> Checked:
        return Checked(
            outcome=ran.outcome,
            slowest_ms=ran.slowest_ms,
            misdeclarations=ran.misdeclarations,
            gate=gate,
            cases=cases or [],
            disagreements=disagreements or [],
        )

    if not settled.agreed:
        return checked(gate=Gate.DISAGREED, disagreements=settled.disagreements)
    if not settled.tested:
        return checked(gate=Gate.UNTESTED)
    return checked(cases=settled.cases)


__all__ = [
    "CAP_MS",
    "Checked",
    "Gate",
    "Ran",
    "agree",
    "check",
    "mistakes",
    "stopped",
    "wrong_on",
]
