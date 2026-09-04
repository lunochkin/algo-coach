"""Storing a problem the runs kept: its cases, both solutions and the match.

Four stores and no atomic write, so the order stands in for one: the problem
is written last, and a run that dies part way leaves orphans rather than a
problem whose parts are missing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from algo_coach import mint
from algo_coach.cases import CaseLog
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
    Call,
    Draft,
    MachineProvenance,
    Problem,
    SettledCase,
    SolutionRole,
    Template,
)
from algo_coach.solutions import SolutionLog


@dataclass(frozen=True)
class Corpus:
    # held together because a problem lands in all four or in none of them
    problems: ProblemStore
    cases: CaseLog
    solutions: SolutionLog
    matches: MatchLog

    @classmethod
    def at(cls, root: Path) -> Corpus:
        return cls(ProblemStore(root), CaseLog(root), SolutionLog(root), MatchLog(root))


def written_by(call: Call) -> dict[str, Any]:
    # one mapping rather than fields a call site can fill partly: a record
    # carries all of a configuration or none of it
    return {
        "model": call.model,
        "effort": call.effort,
        "prompt_hash": call.prompt_hash,
        "call_id": call.id,
        "pin": call.pin or "",
        "temperature": call.temperature,
        "provider": call.provider,
    }


def copied(provenance: MachineProvenance | None) -> dict[str, Any]:
    """The configuration a draft already holds, as `written_by` reads one off a
    call. A step that answered copied it whole, so a missing one is a step the
    draft never took."""
    if provenance is None:
        raise ValueError("a landing draft carries the configuration of every step it took")
    return provenance.model_dump()


def landing(draft: Draft) -> list[SettledCase]:
    """The set the problem carries, in the order it was built: what the two
    solutions settled, then what the rounds won, then the separating case."""
    return [*draft.cases, *draft.won, *([draft.separating] if draft.separating else [])]


def land(corpus: Corpus, template: Template, draft: Draft) -> Problem:
    # minted first, since every other record names its id, and put last, since
    # it is what a reader finds
    written = copied(draft.generator)
    problem = mint.generated_problem(
        draft.title,
        draft.statement,
        generated_for=template.id,
        difficulty=draft.difficulty,
        **written,
    )
    for case in landing(draft):
        # the case's own call rather than the problem's: a mutation round and
        # the speedup search propose arguments at their own configuration
        corpus.cases.append(
            mint.case(
                problem.id,
                case.args,
                case.expected,
                expected_from=case.expected_from,
                round=case.round,
                **written_by(case.call),
            )
        )
    canonical = mint.solution(problem.id, draft.canonical, SolutionRole.CANONICAL, **written)
    corpus.solutions.append(canonical)
    blind = copied(draft.blind)
    if draft.reference is None:
        raise ValueError("a landing draft carries the reference its blind call wrote")
    corpus.solutions.append(
        mint.solution(problem.id, draft.reference, SolutionRole.REFERENCE, **blind)
    )
    corpus.matches.append(mint.generator_match(template.id, canonical.id))
    corpus.problems.put(problem)
    return problem


__all__ = ["Corpus", "copied", "land", "landing", "written_by"]
