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
from algo_coach.generation.speedup import CEILING
from algo_coach.mutation import Mutant, kill, survivors
from algo_coach.runner import NoValue, as_json, outputs
from algo_coach.schema import Call

# what the pass builds at, size-major and smallest first: the input a mutant is
# killed by is the first that kills it, and a small one is a small case
SIZES = (1, 2, 3, 5, 8)
SEEDS = (0, 1, 2, 3)

# how many smaller inputs one shrink may try. Each costs a run of the canonical
# and one per mutant it has to keep killing, so the budget is what stops one
# input spending the pass's whole runtime
TRIES = 24


# what `harden` runs before its first round: the mutants still standing and the
# cap they run under, which the loop paces from the canonical
Fuzzing = Callable[[Sequence["Mutant"], int], "Fuzzed"]


@dataclass(frozen=True)
class Candidate:
    """One built input and the canonical's answer to it, which is what a mutant
    is killed by disagreeing with. Named apart from `inputs.Built`, which is the
    code that produced it."""

    args: list[Any]
    expected: Any


@dataclass(frozen=True)
class Fuzzed:
    """What the pass kept, and what it leaves for a round to ask about."""

    cases: list[SettledCase] = field(default_factory=list)
    standing: list[Mutant] = field(default_factory=list)
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
    through the executor as any other does, and a pair it fails on is dropped."""
    return [one for one in outputs(code, pairs, cap_ms=cap_ms) if isinstance(one, list)]


def pass_over(
    built: Built,
    *,
    canonical: str,
    reference: str,
    call: Call,
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
            call=call,
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
    call: Call,
    cap_ms: int,
    against_ms: int,
    ceiling: int = CEILING,
) -> Fuzzed:
    """Each input against the mutants still standing, keeping the first that
    kills.

    An input that killed nothing is not kept: every later verification would run
    it and it catches nothing. The reference settles the kept ones alone, so an
    input that killed nothing costs no run of it either.
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
        return Fuzzed(standing=standing, built=len(inputs), dropped=dropped)
    args = [one.args for one in kept]
    settled = settle(
        args,
        canonical=[one.expected for one in kept],
        reference=outputs(reference, args, cap_ms=cap_ms),
        call=call,
        # in the set the first round's survivors are decided against, which is
        # what `round` zero names
        round=0,
    )
    return Fuzzed(
        cases=settled.cases,
        standing=standing,
        built=len(inputs),
        dropped=dropped,
        disagreement=settled.disagreements[0] if settled.disagreements else None,
    )


def shrink(
    candidate: Candidate,
    killed: Sequence[Mutant],
    *,
    canonical: str,
    cap_ms: int,
    against_ms: int,
    tries: int = TRIES,
) -> Candidate:
    """The smallest input the search reaches that still kills what this one
    killed.

    A built input is as large as its size asked for, where the mistake it
    catches usually needs a few elements. Every later verification runs the
    stored case, so the shrink is paid once and the size is saved forever.
    """
    kept, left = candidate, tries
    for index, value in enumerate(candidate.args):
        if left <= 0:
            break
        # lists alone: a smaller integer is a different question the statement
        # answers, where a shorter list is the same one asked of less
        if isinstance(value, list) and len(value) > 1:
            kept, left = _ddmin(
                kept,
                index,
                killed,
                canonical=canonical,
                cap_ms=cap_ms,
                against_ms=against_ms,
                left=left,
            )
    return kept


def _ddmin(
    kept: Candidate,
    index: int,
    killed: Sequence[Mutant],
    *,
    canonical: str,
    cap_ms: int,
    against_ms: int,
    left: int,
) -> tuple[Candidate, int]:
    """Delta debugging over one argument, at a granularity that doubles until
    nothing smaller kills.

    The granularity resets on every acceptance rather than carrying over. It
    costs a few more candidates on a long input and it is what keeps one loop
    for both halves of the search.
    """
    sequence = kept.args[index]
    size = 2
    while len(sequence) > 1 and left > 0:
        accepted = None
        for smaller in _subsets(sequence, size):
            if left <= 0:
                break
            left -= 1
            found = _kills(
                kept.args,
                index,
                smaller,
                killed,
                canonical=canonical,
                cap_ms=cap_ms,
                against_ms=against_ms,
            )
            if found is not None:
                kept, accepted = found, smaller
                break
        if accepted is not None:
            sequence, size = accepted, 2
        elif size >= len(sequence):
            break
        else:
            size = min(size * 2, len(sequence))
    return kept, left


def _subsets(sequence: Sequence[Any], size: int) -> list[list[Any]]:
    """What is tried at one granularity: each chunk, then each complement. At
    two chunks the complements are the chunks, so they are not tried twice."""
    chunks = _split(sequence, size)
    if len(chunks) < 3:
        return chunks
    return chunks + [
        [one for other, chunk in enumerate(chunks) if other != index for one in chunk]
        for index in range(len(chunks))
    ]


def _split(sequence: Sequence[Any], size: int) -> list[list[Any]]:
    step = max(len(sequence) // size, 1)
    return [list(sequence[at : at + step]) for at in range(0, len(sequence), step)]


def _kills(
    args: Sequence[Any],
    index: int,
    sequence: Sequence[Any],
    killed: Sequence[Mutant],
    *,
    canonical: str,
    cap_ms: int,
    against_ms: int,
) -> Candidate | None:
    """The input with one argument replaced, where the canonical answers it and
    every mutant the original killed still fails it.

    The canonical is run again because the answer is the input's, and a case
    carrying the old one would fail the solution it was written from.
    """
    smaller = [*args[:index], list(sequence), *args[index + 1 :]]
    [value] = outputs(canonical, [smaller], cap_ms=cap_ms)
    if isinstance(value, NoValue):
        return None
    one = Candidate(args=smaller, expected=value)
    if survivors(kill(killed, [one], cap_ms=against_ms)):
        return None
    return one


def _weighs(value: Any) -> int:
    return len(as_json(value).encode())


__all__ = [
    "SEEDS",
    "SIZES",
    "TRIES",
    "Candidate",
    "Fuzzed",
    "Fuzzing",
    "build",
    "fuzz",
    "grid",
    "pass_over",
    "shrink",
]
