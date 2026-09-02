"""The mutation loop, run over a drafted problem before it lands.

A mutant the case set leaves standing names a case that has to exist, and one
call per round asks for it. `corpus.md` gives the bound the loop stops at.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from algo_coach.calls import CallLog, Transport
from algo_coach.generation.agreement import Disagreement, Settled, SettledCase, settle
from algo_coach.generation.checks import CAP_MS
from algo_coach.generation.discrimination import separators
from algo_coach.generation.generator import DEFAULT, Configuration
from algo_coach.mutation import ROUNDS, Case, kill, mutants, survivors
from algo_coach.runner import NoValue, outputs


@dataclass(frozen=True)
class Hardened:
    """What the rounds won, and what the set still does not catch."""

    cases: list[SettledCase] = field(default_factory=list)
    mutants: int = 0
    survived: int = 0  # mutants no case killed when the loop stopped
    rounds: int = 0  # rounds paid for, at one call each
    dropped: int = 0  # proposals the canonical could not answer
    # a proposed input the two solutions answered differently. The caller
    # discards the problem on it, as it does on any disagreement
    disagreement: Disagreement | None = None


def harden(
    transport: Transport,
    calls: CallLog,
    statement: str,
    *,
    canonical: str,
    reference: str,
    cases: Sequence[Case],
    cap_ms: int = CAP_MS,
    configuration: Configuration = DEFAULT,
    rounds: int = ROUNDS,
) -> Hardened:
    """The cases the mutants force, settled as the first set was.

    A round runs the survivors against what the round before it won alone. The
    cases they already passed cannot kill them.
    """
    standing = mutants(canonical)
    enumerated = len(standing)
    against: Sequence[Case] = cases
    won: list[SettledCase] = []
    dropped = played = 0

    while True:
        before = len(standing)
        standing = [one.mutant for one in survivors(kill(standing, against, cap_ms=cap_ms))]
        if not standing or played == rounds:
            break
        # a round that killed nothing stops the loop: the next one asks the
        # same question of the same survivors
        if played and len(standing) == before:
            break

        played += 1
        proposed, _ = separators(
            transport,
            calls,
            statement,
            canonical=canonical,
            survivors=standing,
            known=[one.args for one in [*cases, *won]],
            configuration=configuration,
        )
        settled = _settled(proposed, canonical=canonical, reference=reference, cap_ms=cap_ms)
        dropped += len(proposed) - len(settled.cases) - len(settled.disagreements)
        if settled.disagreements:
            return _left(won, enumerated, standing, played, dropped, settled.disagreements[0])
        if not settled.cases:
            break
        won.extend(settled.cases)
        against = settled.cases

    return _left(won, enumerated, standing, played, dropped)


def _settled(
    proposed: Sequence[Sequence[Any]],
    *,
    canonical: str,
    reference: str,
    cap_ms: int,
) -> Settled:
    """The proposals the canonical answered, settled by the rule the first case
    set uses.

    One it cannot answer costs the case rather than the problem: nothing checks
    a proposed input against the constraints the statement gives.
    """
    ours = outputs(canonical, proposed, cap_ms=cap_ms)
    answered = [
        (list(args), value)
        for args, value in zip(proposed, ours, strict=True)
        if not isinstance(value, NoValue)
    ]
    args = [one for one, _ in answered]
    theirs = outputs(reference, args, cap_ms=cap_ms)
    return settle(args, canonical=[value for _, value in answered], reference=theirs)


def _left(
    won: list[SettledCase],
    enumerated: int,
    standing: Sequence[Any],
    played: int,
    dropped: int,
    disagreement: Disagreement | None = None,
) -> Hardened:
    return Hardened(
        cases=won,
        mutants=enumerated,
        survived=len(standing),
        rounds=played,
        dropped=dropped,
        disagreement=disagreement,
    )


__all__ = ["Hardened", "harden"]
