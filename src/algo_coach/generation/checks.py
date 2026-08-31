"""Running the two solutions, and whether what they answered lets the problem
land.

Four gates in one pass, in the order `flows.md` runs them. The canonical
yielding no value on some case discards the problem, since nothing establishes
what that case returns. The canonical contradicting the `expected` its own call
declared discards it too: one call wrote the code and the cases, so it wrote
one of the two wrong. A reference that computed no case at all discards it as
well — every expected output would then be the canonical's own, and `verified`
would mean only that the solution agrees with itself. The two solutions
disagreeing discards it last, and that one is the statement's fault rather than
either solution's.

Nothing is repaired. A problem failing any gate is discarded whole, and the
calls that wrote it are already in the log, so what was paid for and thrown
away stays readable.

Executing is the runner's. This decides what the runs mean, and stores
nothing: the ids a case and a solution need do not exist until the problem
lands.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum

from algo_coach.generation.agreement import (
    Disagreement,
    Misdeclaration,
    misdeclared,
    settle,
)
from algo_coach.generation.generator import DraftCase
from algo_coach.runner import NoValue, answered, decide, outputs, run
from algo_coach.schema import CaseOutcome, severest

# The wall-clock cap per case at generation, well above the drill loop's. It
# is what the reference has to finish under, and a case beyond it is where the
# canonical's own answer is taken instead.
CAP_MS = 10_000


class Discard(StrEnum):
    """Why a problem did not survive its runs.

    Named rather than a boolean, because the four are different faults and a
    run reports how its problems were lost. `NO_VALUE` and `MISDECLARED` are
    the generation call's, `DISAGREED` is the statement's, and `UNTESTED` is
    the reference's own reach.
    """

    NO_VALUE = "no_value"
    MISDECLARED = "misdeclared"
    UNTESTED = "untested"
    DISAGREED = "disagreed"


@dataclass(frozen=True)
class Checked:
    """What the two runs decided about one drafted problem.

    `cases` is what would land, carrying the reference's answers, and is empty
    where the problem was discarded. `beyond` is the cases the reference could
    not compute under the cap; taking the canonical's answer on those is the
    step after this one, so they are held apart rather than dropped. A problem
    whose every case is beyond the reference does not survive: nothing
    independent read the statement.

    The failures are carried in full rather than counted. A discarded problem
    is reported by what it disagreed on, and one case says less than all of
    them.
    """

    # how the canonical's run went against what the call declared, folded to
    # its most severe case. `None` only where there were no cases to run
    outcome: CaseOutcome | None
    discard: Discard | None = None
    cases: list[DraftCase] = field(default_factory=list)
    beyond: list[DraftCase] = field(default_factory=list)
    misdeclarations: list[Misdeclaration] = field(default_factory=list)
    disagreements: list[Disagreement] = field(default_factory=list)

    @property
    def survived(self) -> bool:
        return self.discard is None


def check(
    cases: Sequence[DraftCase],
    *,
    canonical: str,
    reference: str,
    cap_ms: int = CAP_MS,
) -> Checked:
    """Run both solutions against the cases, and say whether the problem
    survives.

    The canonical runs first and alone. Where it fails, the reference is never
    run: the two solutions are compared to test the statement, and there is
    nothing to test where the call that wrote the problem contradicted itself.
    """
    args = [case.args for case in cases]
    ran = run(canonical, args, cap_ms=cap_ms)
    ours = [answered(one) for one in ran]
    outcome = severest(decide(one, case.expected) for case, one in zip(cases, ran, strict=True))

    if any(isinstance(one, NoValue) for one in ours):
        return Checked(outcome=outcome, discard=Discard.NO_VALUE)

    wrong = misdeclared(cases, ours)
    if wrong:
        return Checked(outcome=outcome, discard=Discard.MISDECLARED, misdeclarations=wrong)

    theirs = outputs(reference, args, cap_ms=cap_ms)
    reached = [not isinstance(one, NoValue) for one in theirs]
    if not any(reached):
        return Checked(outcome=outcome, discard=Discard.UNTESTED)

    settled = settle(
        [case for case, got in zip(cases, reached, strict=True) if got],
        canonical=[one for one, got in zip(ours, reached, strict=True) if got],
        reference=[one for one, got in zip(theirs, reached, strict=True) if got],
    )
    if not settled.agreed:
        return Checked(
            outcome=outcome, discard=Discard.DISAGREED, disagreements=settled.disagreements
        )
    return Checked(
        outcome=outcome,
        cases=settled.cases,
        beyond=[case for case, got in zip(cases, reached, strict=True) if not got],
    )


__all__ = ["CAP_MS", "Checked", "Discard", "check"]
