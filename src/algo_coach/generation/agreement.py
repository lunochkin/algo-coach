"""Whose answer a case carries, and where the two solutions disagreed.

Outputs are passed in: executing is the runner's, and this reads what a run
means.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from algo_coach.generation.generator import DraftCase
from algo_coach.runner.encoding import agrees
from algo_coach.runner.outputs import NoValue
from algo_coach.schema import Call, ExpectedSource


@dataclass(frozen=True)
class Misdeclaration:
    """One case the canonical answered differently from its call's own `expected`."""

    args: list[Any]
    declared: Any
    returned: Any


def misdeclared(cases: Sequence[DraftCase], canonical: Sequence[Any]) -> list[Misdeclaration]:
    # a gate rather than a source: what a landing case stores is still the
    # reference's answer
    if len(cases) != len(canonical):
        raise ValueError("one output per case, from the canonical")

    return [
        Misdeclaration(args=case.args, declared=case.expected, returned=value)
        for case, value in zip(cases, canonical, strict=True)
        # a case answered with nothing is not a misdeclaration: nothing was
        # computed to compare, and it discards the problem a step later
        if not isinstance(value, NoValue) and not agrees(value, case.expected)
    ]


@dataclass(frozen=True)
class Disagreement:
    """One case the two solutions answered differently."""

    args: list[Any]
    canonical: Any
    reference: Any


@dataclass(frozen=True)
class SettledCase:
    # neither a `TestCase`, which needs a problem id, nor a `DraftCase`, whose
    # `expected` was declared rather than established by a run
    args: list[Any]
    expected: Any
    expected_from: ExpectedSource
    # the call that proposed the arguments, whole rather than by id: the
    # `TestCase` this becomes copies the configuration
    call: Call


@dataclass(frozen=True)
class Settled:
    cases: list[SettledCase] = field(default_factory=list)
    disagreements: list[Disagreement] = field(default_factory=list)

    @property
    def agreed(self) -> bool:
        return not self.disagreements

    @property
    def tested(self) -> list[SettledCase]:
        # the cases that test the canonical rather than restate it
        return [one for one in self.cases if one.expected_from is ExpectedSource.REFERENCE]


def settle(
    args: Sequence[Sequence[Any]],
    *,
    canonical: Sequence[Any],
    reference: Sequence[Any],
    call: Call,
) -> Settled:
    # every case is decided, never stopping at the first disagreement: a
    # discarded problem is reported by every input the two readings differ on
    if not (len(args) == len(canonical) == len(reference)):
        raise ValueError("one output per case, from each solution")

    settled = Settled()
    for one, ours, theirs in zip(args, canonical, reference, strict=True):
        case = list(one)
        if isinstance(theirs, NoValue):
            settled.cases.append(
                SettledCase(
                    args=case,
                    expected=ours,
                    expected_from=ExpectedSource.CANONICAL,
                    call=call,
                )
            )
        elif agrees(ours, theirs):
            settled.cases.append(
                SettledCase(
                    args=case,
                    expected=theirs,
                    expected_from=ExpectedSource.REFERENCE,
                    call=call,
                )
            )
        else:
            settled.disagreements.append(Disagreement(args=case, canonical=ours, reference=theirs))
    return settled
