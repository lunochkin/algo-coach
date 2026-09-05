"""Shrinking a built input to the smallest that still kills what it killed.
`corpus.md` gives what may shrink and against what."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from algo_coach.mutation import Mutant, kill, survivors
from algo_coach.runner import NoValue, outputs

# how many smaller inputs one shrink may try. Each costs a run of the canonical
# and one per mutant it has to keep killing, so the budget is what stops one
# input spending the pass's whole runtime
TRIES = 24


@dataclass(frozen=True)
class Candidate:
    """One built input and the canonical's answer to it, which is what a mutant
    is killed by disagreeing with. Named apart from `inputs.Built`, which is
    the code that produced it."""

    args: list[Any]
    expected: Any


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


__all__ = [
    "TRIES",
    "Candidate",
    "shrink",
]
