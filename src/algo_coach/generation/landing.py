"""Storing a problem the runs kept: its cases, both solutions and the match.

Four stores and no atomic write, so the order stands in for one: the problem
is written last, and a run that dies part way leaves orphans rather than a
problem whose parts are missing.
"""

from dataclasses import dataclass
from pathlib import Path

from algo_coach import mint
from algo_coach.cases import CaseLog
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import (
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


def copied(provenance: MachineProvenance | None) -> MachineProvenance:
    """The configuration a draft already holds. A step that answered copied it
    whole, so a missing one is a step the draft never took."""
    if provenance is None:
        raise ValueError("a landing draft carries the configuration of every step it took")
    return provenance


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
        written=written,
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
                written=case.written,
            )
        )
    canonical = mint.solution(problem.id, draft.canonical, SolutionRole.CANONICAL, written=written)
    corpus.solutions.append(canonical)
    blind = copied(draft.blind)
    if draft.reference is None:
        raise ValueError("a landing draft carries the reference its blind call wrote")
    corpus.solutions.append(
        mint.solution(problem.id, draft.reference, SolutionRole.REFERENCE, written=blind)
    )
    if draft.naive is not None:
        # stored so a later search measures against the solution this run paid
        # for. Absent where the template claims no speedup, since nothing
        # measures a form that is its own optimum
        corpus.solutions.append(
            mint.solution(problem.id, draft.naive, SolutionRole.NAIVE, written=copied(draft.clock))
        )
    corpus.matches.append(mint.generator_match(template.id, canonical.id))
    corpus.problems.put(problem)
    return problem


__all__ = ["Corpus", "copied", "land", "landing"]
