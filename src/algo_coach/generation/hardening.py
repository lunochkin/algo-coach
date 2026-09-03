"""The mutation loop, run over a drafted problem before it lands.

A mutant the case set leaves standing names a case that has to exist, and one
call per round asks for it. `corpus.md` gives the bound the loop stops at.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from time import monotonic
from typing import Any

from algo_coach.calls import CallLog, Configuration, Transport
from algo_coach.generation.agreement import Disagreement, Settled, SettledCase, settle
from algo_coach.generation.checks import CAP_MS
from algo_coach.generation.discrimination import DISCRIMINATION_DEFAULT, separators
from algo_coach.generation.steps import SILENT, Notes
from algo_coach.mutation import ROUNDS, Case, Mutant, kill, mutants, pace, survivors
from algo_coach.runner import NoValue, outputs
from algo_coach.schema import Call


@dataclass(frozen=True)
class Hardened:
    """What the rounds won, and what the set still does not catch."""

    cases: list[SettledCase] = field(default_factory=list)
    mutants: int = 0
    survived: int = 0  # mutants no case killed when the loop stopped
    rounds: int = 0  # rounds paid for, at one call each
    # the last round's call, which is what the counters above were left
    # by. `None` where the first case set killed every mutant
    call: Call | None = None
    dropped: int = 0  # proposals the canonical could not answer
    # a proposed input the two solutions answered differently. The caller
    # discards the problem on it, as it does on any disagreement
    disagreement: Disagreement | None = None


def standing(
    canonical: str,
    cases: Sequence[Case],
    *,
    slowest_ms: int | None = None,
    cap_ms: int = CAP_MS,
) -> list[Mutant]:
    """The mutants the case set leaves alive, which is what a round is asked
    about.

    `harden` runs the same pass itself. A replay needs the survivors before the
    call, since they are in the prompt whose digest decides whether to ask, and
    killing costs subprocesses rather than a call.
    """
    against_ms = pace(slowest_ms, cap_ms=cap_ms)
    return [one.mutant for one in survivors(kill(mutants(canonical), cases, cap_ms=against_ms))]


def harden(
    transport: Transport,
    calls: CallLog,
    statement: str,
    *,
    canonical: str,
    reference: str,
    cases: Sequence[Case],
    slowest_ms: int | None = None,
    cap_ms: int = CAP_MS,
    configuration: Configuration = DISCRIMINATION_DEFAULT,
    rounds: int = ROUNDS,
    notes: Notes = SILENT,
) -> Hardened:
    """The cases the mutants force, settled as the first set was.

    A round runs the survivors against what the round before it won alone. The
    cases they already passed cannot kill them.
    """
    standing = mutants(canonical)
    enumerated = len(standing)
    # paced by the canonical rather than run under the cap the reference needs:
    # a mutant that breaks the loop's progress never returns, and there are
    # dozens of them. `slowest_ms` is what the run that decided the problem
    # measured, so nothing runs the canonical again to time it
    against_ms = pace(slowest_ms, cap_ms=cap_ms)
    notes(
        "mutants",
        f"{enumerated} enumerated, running them under a {against_ms}ms cap",
    )
    against: Sequence[Case] = cases
    won: list[SettledCase] = []
    paid: Call | None = None
    dropped = played = 0

    while True:
        before, started = len(standing), monotonic()
        standing = [one.mutant for one in survivors(kill(standing, against, cap_ms=against_ms))]
        # the runner's own time, which is what the fork server would cut
        notes(
            "mutants",
            f"{before - len(standing)} killed, {len(standing)} standing"
            f", {monotonic() - started:.1f}s in the runner",
        )
        if not standing or played == rounds:
            break
        # a round that killed nothing stops the loop: the next one asks the
        # same question of the same survivors
        if played and len(standing) == before:
            break

        played += 1
        notes("round", f"{played} of {rounds}: asking for the cases that kill {len(standing)}")
        proposed, call = separators(
            transport,
            calls,
            statement,
            canonical=canonical,
            survivors=standing,
            known=[one.args for one in [*cases, *won]],
            configuration=configuration,
        )
        paid = call
        notes("round", f"{played}: {len(proposed)} case(s) proposed", call)
        settled = _settled(
            proposed,
            canonical=canonical,
            reference=reference,
            call=call,
            round=played,
            cap_ms=cap_ms,
        )
        dropped += len(proposed) - len(settled.cases) - len(settled.disagreements)
        notes("round", f"{played}: {len(settled.cases)} won, {dropped} dropped")
        if settled.disagreements:
            return _left(won, enumerated, standing, played, dropped, paid, settled.disagreements[0])
        if not settled.cases:
            break
        won.extend(settled.cases)
        against = settled.cases

    return _left(won, enumerated, standing, played, dropped, paid)


def _settled(
    proposed: Sequence[Sequence[Any]],
    *,
    canonical: str,
    reference: str,
    call: Call,
    round: int,
    cap_ms: int,
) -> Settled:
    """The proposals the canonical answered, settled by the rule the first case
    set uses.

    One it cannot answer costs the case rather than the problem.
    """
    ours = outputs(canonical, proposed, cap_ms=cap_ms)
    answered = [
        (list(args), value)
        for args, value in zip(proposed, ours, strict=True)
        if not isinstance(value, NoValue)
    ]
    args = [one for one, _ in answered]
    theirs = outputs(reference, args, cap_ms=cap_ms)
    return settle(
        args,
        canonical=[value for _, value in answered],
        reference=theirs,
        call=call,
        round=round,
    )


def _left(
    won: list[SettledCase],
    enumerated: int,
    standing: Sequence[Any],
    played: int,
    dropped: int,
    call: Call | None,
    disagreement: Disagreement | None = None,
) -> Hardened:
    return Hardened(
        cases=won,
        mutants=enumerated,
        survived=len(standing),
        rounds=played,
        dropped=dropped,
        call=call,
        disagreement=disagreement,
    )


__all__ = ["Hardened", "harden", "standing"]
