"""Storing a problem the runs kept: its cases, both solutions and the match.

Four stores and no atomic write, so the order stands in for one: the problem
is written last, and a run that dies part way leaves orphans rather than a
problem whose parts are missing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from algo_coach import mint
from algo_coach.cases import CaseLog
from algo_coach.generation.generator import Generated
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Call, Problem, SettledCase, SolutionRole, Template
from algo_coach.solutions import SolutionLog


class Drafted(BaseModel):
    """One problem the two calls wrote, and what its runs left. Nothing is
    stored yet."""

    draft: Generated
    solution: str  # the reference, written from the statement alone
    # whole rather than by id: every record this becomes copies a configuration
    call: Call
    reference_call: Call
    # what the runs established, where `draft.cases` holds what was declared
    cases: list[SettledCase] = Field(default_factory=list)


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


def land(corpus: Corpus, template: Template, drafted: Drafted) -> Problem:
    # minted first, since every other record names its id, and put last, since
    # it is what a reader finds
    draft = drafted.draft
    problem = mint.generated_problem(
        draft.title,
        draft.statement,
        generated_for=template.id,
        difficulty=draft.difficulty,
        **written_by(drafted.call),
    )
    for case in drafted.cases:
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
    canonical = mint.solution(
        problem.id, draft.canonical, SolutionRole.CANONICAL, **written_by(drafted.call)
    )
    corpus.solutions.append(canonical)
    corpus.solutions.append(
        mint.solution(
            problem.id,
            drafted.solution,
            SolutionRole.REFERENCE,
            **written_by(drafted.reference_call),
        )
    )
    corpus.matches.append(mint.generator_match(template.id, canonical.id))
    corpus.problems.put(problem)
    return problem


__all__ = ["Corpus", "Drafted", "land", "written_by"]
