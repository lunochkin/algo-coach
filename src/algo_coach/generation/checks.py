"""Running the two solutions, and whether what they answered lets the problem land.

Stores nothing: the ids a case and a solution need do not exist until it lands.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from algo_coach.generation.agreement import (
    Disagreement,
    Misdeclaration,
    SettledCase,
    misdeclared,
    settle,
)
from algo_coach.generation.generator import DraftCase
from algo_coach.runner import NoValue, answered, decide, outputs, run
from algo_coach.schema import CaseOutcome, Discard, severest

# the per-case cap at generation, well above the drill loop's: what the
# reference has to finish under
CAP_MS = 10_000


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


def check(
    cases: Sequence[DraftCase],
    *,
    canonical: str,
    reference: str,
    cap_ms: int = CAP_MS,
) -> Checked:
    # the canonical first and alone: comparing the two tests the statement,
    # and a call that contradicted itself leaves nothing to test
    args = [case.args for case in cases]
    ran = run(canonical, args, cap_ms=cap_ms)
    ours = [answered(one) for one in ran]
    outcome = severest(decide(one, case.expected) for case, one in zip(cases, ran, strict=True))
    slowest = max((one.elapsed_ms or 0 for one in ran if one.returned), default=0)

    if any(isinstance(one, NoValue) for one in ours):
        return Checked(outcome=outcome, slowest_ms=slowest, discard=Discard.NO_VALUE)

    wrong = misdeclared(cases, ours)
    if wrong:
        return Checked(
            outcome=outcome,
            slowest_ms=slowest,
            discard=Discard.MISDECLARED,
            misdeclarations=wrong,
        )

    theirs = outputs(reference, args, cap_ms=cap_ms)
    settled = settle(args, canonical=ours, reference=theirs)
    if not settled.agreed:
        return Checked(
            outcome=outcome,
            slowest_ms=slowest,
            discard=Discard.DISAGREED,
            disagreements=settled.disagreements,
        )
    if not settled.tested:
        return Checked(outcome=outcome, slowest_ms=slowest, discard=Discard.UNTESTED)
    return Checked(outcome=outcome, slowest_ms=slowest, cases=settled.cases)


__all__ = ["CAP_MS", "Checked", "Discard", "check"]
