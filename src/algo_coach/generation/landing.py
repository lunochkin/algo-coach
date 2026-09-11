"""Storing a problem the runs kept: its cases, both solutions and the match.

Four stores and no atomic write, so the order stands in for one: the problem
is written last, and a run that dies part way leaves orphans rather than a
problem whose parts are missing.
"""

from dataclasses import dataclass

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
from algo_coach.storage import Database


@dataclass(frozen=True)
class Corpus:
    # held together because a problem lands in all four or in none of them
    problems: ProblemStore
    cases: CaseLog
    solutions: SolutionLog
    matches: MatchLog

    @classmethod
    def at(cls, root: Database) -> Corpus:
        return cls(ProblemStore(root), CaseLog(root), SolutionLog(root), MatchLog(root))


def copied(provenance: MachineProvenance | None) -> MachineProvenance:
    """The configuration a draft already holds. A step that answered copied it
    whole, so a missing one is a step the draft never took."""
    if provenance is None:
        raise ValueError("a landing draft carries the configuration of every step it took")
    return provenance


def landing(draft: Draft) -> list[SettledCase]:
    """The set the problem carries, in the order it was built: what the two
    solutions settled, what the fuzz pass kept, what the rounds won, then the
    separating case."""
    return [
        *draft.cases,
        *draft.kept,
        *draft.won,
        *([draft.separating_case] if draft.separating_case else []),
    ]


def land(corpus: Corpus, template: Template, draft: Draft) -> Problem:
    # minted first, since every other record names its id, and put last, since
    # it is what a reader finds
    provenance = copied(draft.generator_provenance)
    problem = mint.generated_problem(
        draft.title,
        draft.statement,
        target_template_id=template.id,
        difficulty=draft.difficulty,
        provenance=provenance,
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
                repeats=case.repeats,
                provenance=case.provenance,
            )
        )
    canonical = mint.solution(
        problem.id, draft.canonical, SolutionRole.CANONICAL, provenance=provenance
    )
    corpus.solutions.append(canonical)
    blind = copied(draft.blind_provenance)
    if draft.reference is None:
        raise ValueError("a landing draft carries the reference its blind call wrote")
    corpus.solutions.append(
        mint.solution(problem.id, draft.reference, SolutionRole.REFERENCE, provenance=blind)
    )
    if draft.naive is not None:
        # stored so a later search measures against the solution this run paid
        # for. Absent where the template claims no speedup, since nothing
        # measures a form that is its own optimum
        corpus.solutions.append(
            mint.solution(
                problem.id,
                draft.naive,
                SolutionRole.NAIVE,
                provenance=copied(draft.naive_provenance),
            )
        )
    corpus.matches.append(mint.generator_match(template.id, canonical.id))
    corpus.problems.put(problem)
    return problem


__all__ = ["Corpus", "copied", "land", "landing"]
