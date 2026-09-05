"""The fuzz pass: inputs the generator builds, run against the mutants the case
set left standing.

It costs subprocesses where a round costs a call, so it runs before any round
and only the mutants it leaves standing are asked about.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from algo_coach.generation.agreement import Disagreement, SettledCase, settle
from algo_coach.generation.inputs import Built
from algo_coach.generation.shrinking import Candidate, shrink
from algo_coach.generation.speedup import CEILING
from algo_coach.mutation import Mutant, kill, survivors
from algo_coach.runner import NoValue, as_json, outputs
from algo_coach.schema import MachineProvenance

# what the pass builds at, size-major and smallest first: the input a mutant is
# killed by is the first that kills it, and a small one is a small case
SIZES = (1, 2, 3, 5, 8)


SEEDS = (0, 1, 2, 3)


# what `harden` runs before its first round: the mutants still standing and the
# cap they run under, which the loop paces from the canonical
Fuzzing = Callable[[Sequence["Mutant"], int], "Fuzzed"]


@dataclass(frozen=True)
class Fuzzed:
    """What the pass kept, and what it leaves for a round to ask about."""

    cases: list[SettledCase] = field(default_factory=list)
    standing: list[Mutant] = field(default_factory=list)
    killed: int = 0  # mutants the kept inputs caught
    built: int = 0  # inputs the generator's code produced
    dropped: int = 0  # of those, the ones the canonical could not answer
    # a kept input the two solutions answered differently. The caller discards
    # the problem on it, as it does on a round's
    disagreement: Disagreement | None = None


def grid(
    largest: int, *, sizes: Sequence[int] = SIZES, seeds: Sequence[int] = SEEDS
) -> list[list[int]]:
    """The pairs to build at, never above the size the statement allows."""
    return [[size, seed] for size in sizes if size <= largest for seed in seeds]


def build(code: str, pairs: Sequence[Sequence[int]], *, cap_ms: int) -> list[list[Any]]:
    """Every pair in one batch. The generator is model-written code, so it runs
    through the executor as any other does, and a pair it fails on is
    dropped."""
    return [one for one in outputs(code, pairs, cap_ms=cap_ms) if isinstance(one, list)]


def pass_over(
    built: Built,
    *,
    canonical: str,
    reference: str,
    written: MachineProvenance,
    cap_ms: int,
) -> Fuzzing:
    """`fuzz` bound to one problem, which is the shape `harden` runs.

    The inputs are built inside it rather than here, so a case set that already
    kills every mutant pays for no subprocess.
    """
    pairs = grid(built.largest)

    def over(standing: Sequence[Mutant], against_ms: int) -> Fuzzed:
        return fuzz(
            standing,
            build(built.code, pairs, cap_ms=cap_ms),
            canonical=canonical,
            reference=reference,
            written=written,
            cap_ms=cap_ms,
            against_ms=against_ms,
        )

    return over


def fuzz(
    mutants: Sequence[Mutant],
    inputs: Sequence[Sequence[Any]],
    *,
    canonical: str,
    reference: str,
    written: MachineProvenance,
    cap_ms: int,
    against_ms: int,
    ceiling: int = CEILING,
) -> Fuzzed:
    """Each input against the mutants still standing, keeping the first that
    kills.

    An input that killed nothing is not kept: every later verification would
    run it and it catches nothing. The reference settles the kept ones alone,
    so an input that killed nothing costs no run of it either.
    """
    standing = list(mutants)
    # one batch, though the loop stops as soon as nothing stands: the runner
    # starts a batch's children together, where one input at a time serialises
    answers = outputs(canonical, [list(one) for one in inputs], cap_ms=cap_ms)
    kept: list[Candidate] = []
    dropped = 0

    for args, value in zip(inputs, answers, strict=True):
        if not standing:
            break
        if isinstance(value, NoValue):
            # as a proposed case the canonical cannot answer: nothing checks a
            # built input against the constraints the statement gives
            dropped += 1
            continue
        one = Candidate(args=list(args), expected=value)
        left = [each.mutant for each in survivors(kill(standing, [one], cap_ms=against_ms))]
        if len(left) == len(standing):
            continue
        one = shrink(
            one,
            [each for each in standing if each not in left],
            canonical=canonical,
            cap_ms=cap_ms,
            against_ms=against_ms,
        )
        # after the shrink rather than before it: an input the ceiling rejects
        # is storable once it is only as large as the kill needs
        if _weighs(one.args) + _weighs(one.expected) > ceiling:
            continue
        standing = left
        kept.append(one)

    if not kept:
        return Fuzzed(
            standing=standing,
            killed=len(mutants) - len(standing),
            built=len(inputs),
            dropped=dropped,
        )
    args = [one.args for one in kept]
    settled = settle(
        args,
        canonical=[one.expected for one in kept],
        reference=outputs(reference, args, cap_ms=cap_ms),
        written=written,
        # in the set the first round's survivors are decided against, which is
        # what `round` zero names
        round=0,
    )
    return Fuzzed(
        cases=settled.cases,
        standing=standing,
        killed=len(mutants) - len(standing),
        built=len(inputs),
        dropped=dropped,
        disagreement=settled.disagreements[0] if settled.disagreements else None,
    )


def _weighs(value: Any) -> int:
    return len(as_json(value).encode())


__all__ = [
    "SEEDS",
    "SIZES",
    "Fuzzed",
    "Fuzzing",
    "build",
    "fuzz",
    "grid",
    "pass_over",
]
