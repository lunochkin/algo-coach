"""Running the two solutions, and whether what they answered lets the problem
land.

Two steps rather than one, in the order `flows.md` gives: the canonical is run
and read against what its own call declared, and only then is it settled
against a reference. The reading discards nothing, since one call wrote both.

Stores nothing: the ids a case and a solution need do not exist until it lands.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from algo_coach.generation.agreement import (
    Disagreement,
    Misdeclaration,
    SettledCase,
    misdeclared,
    settle,
)
from algo_coach.runner import NoValue, agrees, answered, decide, outputs, run
from algo_coach.schema import CaseOutcome, Discard, DraftCase, MachineProvenance, severest

# the per-case cap at generation, well above the drill loop's: what the
# reference has to finish under
CAP_MS = 10_000


@dataclass(frozen=True)
class Ran:
    """The canonical's own run, before any reference exists. `returned` is what
    it answered, kept so the settling does not run it a second time."""

    outcome: CaseOutcome | None
    slowest_ms: int | None = None
    returned: list[Any] = field(default_factory=list)
    discard: Discard | None = None
    misdeclarations: list[Misdeclaration] = field(default_factory=list)

    @property
    def survived(self) -> bool:
        return self.discard is None


@dataclass(frozen=True)
class Checked:
    """What the two runs decided about one drafted problem. `cases` is empty
    where it was discarded."""

    # the canonical's run against what its call declared, folded to the
    # severest case. `None` only where there were no cases to run
    outcome: CaseOutcome | None
    # what the canonical's slowest case took in that run. The mutation loop
    # paces its cap by it rather than running the canonical again
    slowest_ms: int | None = None
    discard: Discard | None = None
    cases: list[SettledCase] = field(default_factory=list)
    misdeclarations: list[Misdeclaration] = field(default_factory=list)
    disagreements: list[Disagreement] = field(default_factory=list)

    @property
    def survived(self) -> bool:
        return self.discard is None


def mistakes(cases: Sequence[SettledCase], *, code: str, cap_ms: int = CAP_MS) -> list[SettledCase]:
    """The cases a solution answered and got wrong.

    A case it did not finish is not among them: being slow is what the clock is
    for, and only a computed answer can be wrong.
    """
    ran = outputs(code, [case.args for case in cases], cap_ms=cap_ms)
    return [
        case
        for case, value in zip(cases, ran, strict=True)
        if not isinstance(value, NoValue) and not agrees(value, case.expected)
    ]


def check(cases: Sequence[DraftCase], *, canonical: str, cap_ms: int = CAP_MS) -> Ran:
    """The canonical alone, before a blind call is paid for. A case it answered
    differently from its own call's `expected` is counted rather than gated:
    one call wrote the code and the declaration, so they share a reading."""
    args = [case.args for case in cases]
    ran = run(canonical, args, cap_ms=cap_ms)
    ours = [answered(one) for one in ran]
    outcome = severest(decide(one, case.expected) for case, one in zip(cases, ran, strict=True))
    slowest = max((one.elapsed_ms or 0 for one in ran if one.returned), default=0)

    if any(isinstance(one, NoValue) for one in ours):
        return Ran(outcome=outcome, slowest_ms=slowest, discard=Discard.NO_VALUE)

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
        discard=ran.discard,
        misdeclarations=ran.misdeclarations,
    )


def agree(
    ran: Ran,
    cases: Sequence[DraftCase],
    *,
    reference: str,
    written: MachineProvenance,
    cap_ms: int = CAP_MS,
) -> Checked:
    """The reference against the canonical's answers, which is what settles a
    case. The canonical is not run again: `ran` carries what it returned.

    `written` is the generator's configuration rather than the blind call's:
    the arguments are the statement's own cases, whoever computed what they
    return."""
    args = [case.args for case in cases]
    theirs = outputs(reference, args, cap_ms=cap_ms)
    settled = settle(args, canonical=ran.returned, reference=theirs, written=written)
    # carried rather than dropped at the gate it no longer is: the count is
    # what the generator's own record is scored on
    kept = {
        "outcome": ran.outcome,
        "slowest_ms": ran.slowest_ms,
        "misdeclarations": ran.misdeclarations,
    }
    if not settled.agreed:
        return Checked(**kept, discard=Discard.DISAGREED, disagreements=settled.disagreements)
    if not settled.tested:
        return Checked(**kept, discard=Discard.UNTESTED)
    return Checked(**kept, cases=settled.cases)


__all__ = ["CAP_MS", "Checked", "Discard", "Ran", "agree", "check", "mistakes", "stopped"]
