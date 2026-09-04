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
from algo_coach.generation.fuzzing import Fuzzed, Fuzzing
from algo_coach.generation.steps import SILENT, Notes
from algo_coach.mutation import ROUNDS, Case, Mutant, kill, mutants, pace, survivors
from algo_coach.runner import NoValue, outputs
from algo_coach.schema import Call, MachineProvenance


@dataclass(frozen=True)
class Hardened:
    """What the rounds won, and what the set still does not catch."""

    cases: list[SettledCase] = field(default_factory=list)
    mutants: int = 0
    survived: int = 0  # mutants no case killed when the loop stopped
    rounds: int = 0  # rounds paid for, at one call each
    fuzzed: Fuzzed | None = None  # the pass before the rounds, where one ran
    # which source killed what, so a report can say whether a round earned its
    # call: the set the loop was given, then one entry per round it played
    declared: int = 0
    caught: list[int] = field(default_factory=list)
    # the last round's call, which is what the counters above were left
    # by. `None` where the first case set killed every mutant
    call: Call | None = None
    dropped: int = 0  # proposals the canonical could not answer
    # proposals a round put to the set, landed or not. What the rounds landed
    # is `cases` minus the fuzz pass's, so the difference is what killed
    # nothing
    offered: int = 0
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
    fuzzing: Fuzzing | None = None,
    notes: Notes = SILENT,
) -> Hardened:
    """The cases the mutants force, settled as the first set was.

    A round runs the survivors against what the round before it won alone. The
    cases they already passed cannot kill them.

    `fuzzing` is the pass before the first round: it costs subprocesses rather
    than a call, so what it kills is never asked about.
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
    won: list[SettledCase] = []
    # every settled proposal, landed or not: a dropped one leaves `won`, and a
    # round shown neither can propose an input that already killed nothing
    asked: list[Sequence[Any]] = []
    paid: Call | None = None
    fuzzed: Fuzzed | None = None
    caught: list[int] = []
    dropped = played = offered = 0

    started = monotonic()
    standing = [one.mutant for one in survivors(kill(standing, cases, cap_ms=against_ms))]
    declared = enumerated - len(standing)
    # the runner's own time, which is what the fork server would cut
    notes(
        "mutants",
        f"{declared} killed, {len(standing)} standing, {monotonic() - started:.1f}s in the runner",
    )

    if standing and fuzzing is not None:
        fuzzed = fuzzing(standing, against_ms)
        notes(
            "fuzz",
            f"{fuzzed.built} built, {len(fuzzed.cases)} kept, {len(fuzzed.standing)} standing",
        )
        won.extend(fuzzed.cases)
        standing = fuzzed.standing
        if fuzzed.disagreement is not None:
            return _left(
                won=won,
                enumerated=enumerated,
                standing=standing,
                played=played,
                dropped=dropped,
                offered=offered,
                declared=declared,
                caught=caught,
                call=paid,
                fuzzed=fuzzed,
                disagreement=fuzzed.disagreement,
            )

    while standing and played < rounds:
        played += 1
        notes("round", f"{played} of {rounds}: asking for the cases that kill {len(standing)}")
        proposed, call = separators(
            transport,
            calls,
            statement,
            canonical=canonical,
            survivors=standing,
            known=[*[one.args for one in [*cases, *won]], *asked],
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
        if settled.disagreements:
            return _left(
                won=won,
                enumerated=enumerated,
                standing=standing,
                played=played,
                dropped=dropped,
                offered=offered,
                declared=declared,
                caught=caught,
                call=paid,
                fuzzed=fuzzed,
                disagreement=settled.disagreements[0],
            )
        if not settled.cases:
            break

        offered += len(settled.cases)
        asked.extend(one.args for one in settled.cases)
        before, started = len(standing), monotonic()
        killers, standing = _killers(standing, settled.cases, cap_ms=against_ms)
        caught.append(before - len(standing))
        notes(
            "round",
            f"{played}: {len(killers)} of {len(settled.cases)} landed"
            f", {len(standing)} standing, {monotonic() - started:.1f}s in the runner",
        )
        won.extend(killers)
        # a round whose proposals killed nothing stops the loop: the next one
        # asks the same question of the same survivors
        if not killers:
            break

    return _left(
        won=won,
        enumerated=enumerated,
        standing=standing,
        played=played,
        dropped=dropped,
        offered=offered,
        declared=declared,
        caught=caught,
        call=paid,
        fuzzed=fuzzed,
    )


def _killers(
    standing: Sequence[Mutant], cases: Sequence[Case], *, cap_ms: int
) -> tuple[list[Any], list[Mutant]]:
    """The proposals that killed, and the mutants left standing.

    A mutant names the first case that failed it, so a proposal no mutant names
    killed nothing. Two proposals killing one mutant land the first: the second
    decides nothing the set does not already decide.
    """
    verdicts = kill(standing, cases, cap_ms=cap_ms)
    named = {one.case for one in verdicts if not one.survived}
    return (
        [one for at, one in enumerate(cases) if at in named],
        [one.mutant for one in survivors(verdicts)],
    )


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
        written=MachineProvenance.of(call),
        round=round,
    )


def _left(
    *,
    won: list[SettledCase],
    enumerated: int,
    standing: Sequence[Any],
    played: int,
    dropped: int,
    offered: int,
    declared: int,
    caught: list[int],
    call: Call | None,
    fuzzed: Fuzzed | None = None,
    disagreement: Disagreement | None = None,
) -> Hardened:
    return Hardened(
        cases=won,
        mutants=enumerated,
        survived=len(standing),
        rounds=played,
        dropped=dropped,
        offered=offered,
        call=call,
        disagreement=disagreement,
        fuzzed=fuzzed,
        declared=declared,
        caught=list(caught),
    )


__all__ = ["Hardened", "harden", "standing"]
