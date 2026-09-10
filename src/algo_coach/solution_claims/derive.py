"""What solving a problem can take. A view, never stored truth."""

from collections.abc import Iterable
from pathlib import Path

from algo_coach.problems.store import ProblemStore
from algo_coach.schema import Problem, Solution, SolutionClaim, SolutionRole
from algo_coach.solution_claims.standing import standing_solution_claims
from algo_coach.solution_claims.store import SolutionClaimLog
from algo_coach.solutions.store import SolutionLog


def derive(
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    claims: Iterable[SolutionClaim],
) -> dict[str, list[str]]:
    """The techniques each problem's canonicals were read as, keyed by problem.

    The reference is excluded, for the reason `corpus.md` gives. A canonical
    nothing has read contributes nothing, which is not a verdict that it used
    no technique.
    """
    standing = standing_solution_claims(claims)
    derived: dict[str, set[str]] = {problem.id: set() for problem in problems}
    for solution in solutions:
        if solution.role is not SolutionRole.CANONICAL or solution.problem_id not in derived:
            continue
        claim = standing.get(solution.id)
        if claim is not None:
            derived[solution.problem_id] |= set(claim.techniques)
    # sorted: a claim's prompt is rendered from these, and the prompt hash is
    # taken over that text.
    return {problem_id: sorted(codes) for problem_id, codes in derived.items()}


def with_techniques(
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    claims: Iterable[SolutionClaim],
) -> list[Problem]:
    """Each problem carrying the view rather than what its record stores."""
    problems = list(problems)
    derived = derive(problems, solutions, claims)
    return [problem.model_copy(update={"techniques": derived[problem.id]}) for problem in problems]


def load_problems(root: Path) -> list[Problem]:
    """Every stored problem carrying the view. The store alone returns the
    record, whose `techniques` is empty on every generated problem."""
    return with_techniques(
        ProblemStore(root).all(), SolutionLog(root).solutions(), SolutionClaimLog(root).claims()
    )
