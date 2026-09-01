"""Storing a problem the runs kept: the statement, its cases, both solutions
and the match generation asserts.

One act, because the parts are only a problem together. A statement with no
cases is one nothing can judge, and a problem with no canonical is a rung that
teaches nothing — yet the matcher reads whatever the problem store holds and
has no way to tell either from a finished one.

Four stores cannot be written atomically, so the order stands in for it.
Everything keyed to the problem is written first and the problem itself last:
a run that dies part way leaves records pointing at a problem no reader finds,
rather than a problem whose parts are missing.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from algo_coach import mint
from algo_coach.cases import CaseLog
from algo_coach.generation.agreement import SettledCase
from algo_coach.generation.generator import Draft
from algo_coach.matches import MatchLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import Call, Problem, SolutionRole, Template
from algo_coach.solutions import SolutionLog


class Drafted(BaseModel):
    """One problem the two calls wrote, and what its runs left.

    Called drafted rather than generated because nothing is stored yet. What
    lands is `cases`, each naming the solution that computed its answer, where
    `draft.cases` holds the values the generation call declared, which the runs
    read as a gate rather than as a source.

    Both calls are carried whole rather than by id. Every record this becomes
    copies its configuration from one of them, and a record whose configuration
    is partly unknown compares with nothing.
    """

    draft: Draft
    solution: str  # the reference, written from the statement alone
    call: Call  # what wrote the problem
    reference_call: Call
    # what the runs established, which is what a landing case stores
    cases: list[SettledCase] = Field(default_factory=list)


@dataclass(frozen=True)
class Corpus:
    """The stores one landing writes to, and the run reads its history from.

    Held together because a problem lands in all four or in none of them. A
    caller handed three of them would write a problem missing a part, which is
    what the one act exists to prevent.
    """

    problems: ProblemStore
    cases: CaseLog
    solutions: SolutionLog
    matches: MatchLog

    @classmethod
    def at(cls, root: Path) -> Corpus:
        return cls(ProblemStore(root), CaseLog(root), SolutionLog(root), MatchLog(root))


def written_by(call: Call) -> dict[str, Any]:
    """The configuration a record copies from the call that produced it.

    All of it or none, so it travels as one mapping rather than as fields a
    call site can fill partly.
    """
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
    """Store one problem whole, and return it.

    The problem is minted first, since every other record names its id, and
    written last, since it is what a reader finds.

    Each solution carries the configuration of the call that wrote it: the
    canonical came from the generation call, the reference from its own. The
    problem carries the generation call's, which is the act that wrote it.

    The techniques are left empty. They are a view over the problem's canonical
    solutions, and deriving them is its own step.
    """
    draft = drafted.draft
    problem = mint.generated_problem(
        draft.title,
        draft.statement,
        generated_for=template.id,
        difficulty=draft.difficulty,
        **written_by(drafted.call),
    )
    for case in drafted.cases:
        corpus.cases.append(
            mint.case(problem.id, case.args, case.expected, expected_from=case.expected_from)
        )
    corpus.solutions.append(
        mint.solution(
            problem.id, draft.canonical, SolutionRole.CANONICAL, **written_by(drafted.call)
        )
    )
    corpus.solutions.append(
        mint.solution(
            problem.id,
            drafted.solution,
            SolutionRole.REFERENCE,
            **written_by(drafted.reference_call),
        )
    )
    corpus.matches.append(mint.generator_match(template.id, problem.id))
    corpus.problems.put(problem)
    return problem


__all__ = ["Corpus", "Drafted", "land", "written_by"]
