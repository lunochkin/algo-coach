"""Whether the two solutions read the statement the same way, and whose answer
a case carries.

The canonical and the reference are run against the same arguments. Where they
answer differently the prose admits two readings, and the problem is discarded
rather than repaired: a corrected statement drags its cases with it, so there
is nothing to keep.

Where they agree, the stored expected output is still the reference's. A case
the canonical produced passes by construction, and `verified` would then mean
only that the solution agrees with itself.

The outputs are passed in rather than produced here. Executing a solution is
the runner's, and this decides what the run means.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from algo_coach.generation.generator import DraftCase


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


def as_json(value: Any) -> str:
    """A value as the case will store it.

    Agreement is agreement as JSON, because that is what a stored case holds.
    A tuple and a list are one answer under that rule, where `True` and `1`
    are two. A value JSON cannot hold is not a case at all, and the encoder
    raising here says so.
    """
    return json.dumps(value, sort_keys=True)


def agrees(canonical: Any, reference: Any) -> bool:
    return as_json(canonical) == as_json(reference)


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
