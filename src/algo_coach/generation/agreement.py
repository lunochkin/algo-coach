"""Whether the two solutions read the statement the same way, and whose answer
a case carries.

Two comparisons, at two points. The canonical is first read against the
`expected` the same call declared beside it: one call wrote both, so a
disagreement there means it wrote one of the two wrong. Then the canonical and
the reference are read against each other.

The canonical and the reference are run against the same arguments. Where they
answer differently the prose admits two readings, and the problem is discarded
rather than repaired: a corrected statement drags its cases with it, so there
is nothing to keep.

Where they agree, the stored expected output is still the reference's. A case
the canonical produced passes by construction, and `verified` would then mean
only that the solution agrees with itself.

The outputs are passed in rather than produced here. Executing a solution is
the runner's, and this decides what the run means. Agreement is agreement as
JSON, by the rule the runner encodes a return with.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from algo_coach.generation.generator import DraftCase
from algo_coach.runner.encoding import agrees
from algo_coach.runner.outputs import NoValue


@dataclass(frozen=True)
class Misdeclaration:
    """One case the canonical answered differently from what the call that
    wrote it declared.

    Carries both, as a `Disagreement` does. Which of the two is wrong is not
    the question here either: one call wrote the code and the case, and the
    pair is what shows it wrote one of them wrong.
    """

    args: list[Any]
    declared: Any
    returned: Any


def misdeclared(cases: Sequence[DraftCase], canonical: Sequence[Any]) -> list[Misdeclaration]:
    """Every case the canonical answered differently from its declared
    `expected`.

    A gate rather than a source. What a landing case stores is still the
    reference's answer, and the generator's own values are read only to catch
    a call whose code and cases did not come from one reading of the
    statement.

    A case the canonical answered with nothing is not a misdeclaration.
    Nothing was computed to compare, and yielding no value is what discards
    the problem a step later.

    The outputs line up with the cases positionally, as they do in `settle`. A
    run that answered a different number of them is a fault in the runner.
    """
    if len(cases) != len(canonical):
        raise ValueError("one output per case, from the canonical")

    return [
        Misdeclaration(args=case.args, declared=case.expected, returned=value)
        for case, value in zip(cases, canonical, strict=True)
        if not isinstance(value, NoValue) and not agrees(value, case.expected)
    ]


@dataclass(frozen=True)
class Disagreement:
    """One case the two solutions answered differently.

    Carries both answers, since which of them is wrong is not the question:
    the statement is what admitted two readings, and the pair is what shows it.
    """

    args: list[Any]
    canonical: Any
    reference: Any


@dataclass(frozen=True)
class Settled:
    """What the two runs decided: the cases as they would be stored, and every
    case the solutions answered differently.

    Both, rather than one or the other. A discarded problem is reported by
    what it disagreed on, and the cases are what a landing problem carries.
    """

    cases: list[DraftCase] = field(default_factory=list)
    disagreements: list[Disagreement] = field(default_factory=list)

    @property
    def agreed(self) -> bool:
        return not self.disagreements


def settle(
    cases: Sequence[DraftCase],
    *,
    canonical: Sequence[Any],
    reference: Sequence[Any],
) -> Settled:
    """The cases with the reference's answers, and what the two disagreed on.

    Every case is decided, never stopping at the first disagreement: which
    inputs the two readings differ on is what a discarded problem is reported
    by, and one of them says less than all of them.

    The outputs line up with the cases positionally. A run that answered a
    different number of them decided nothing here, and is a fault in the
    runner rather than a disagreement between the solutions.
    """
    if not (len(cases) == len(canonical) == len(reference)):
        raise ValueError("one output per case, from each solution")

    settled = Settled()
    for case, ours, theirs in zip(cases, canonical, reference, strict=True):
        if agrees(ours, theirs):
            # Copied rather than rebuilt: a case decodes its JSON on the way
            # in, and a decoded string would be decoded a second time.
            settled.cases.append(case.model_copy(update={"expected": theirs}))
        else:
            settled.disagreements.append(
                Disagreement(args=case.args, canonical=ours, reference=theirs)
            )
    return settled
