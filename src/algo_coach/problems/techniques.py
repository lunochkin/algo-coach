"""What solving a problem can take: the union over the standing readings of its
canonicals. A view, never stored truth."""

from collections.abc import Iterable

from algo_coach.readings.standing import standing_readings
from algo_coach.schema import Problem, Solution, SolutionRole, TechniqueReading


def derive(
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    readings: Iterable[TechniqueReading],
) -> dict[str, list[str]]:
    """The techniques each problem's canonicals were read as, keyed by problem.

    The reference is excluded: it is written from the statement alone, so
    counting it would credit the naive approach the canonical's form replaces.
    A canonical nothing has read contributes nothing, which is not a verdict
    that it used no technique.
    """
    standing = standing_readings(readings)
    derived: dict[str, set[str]] = {problem.id: set() for problem in problems}
    for solution in solutions:
        if solution.role is not SolutionRole.CANONICAL or solution.problem_id not in derived:
            continue
        reading = standing.get(solution.id)
        if reading is not None:
            derived[solution.problem_id] |= set(reading.techniques)
    # sorted: a claim's prompt is rendered from these, and the digest is taken
    # over that text.
    return {problem_id: sorted(codes) for problem_id, codes in derived.items()}


def with_techniques(
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    readings: Iterable[TechniqueReading],
) -> list[Problem]:
    """Each problem carrying the view rather than what its record stores."""
    problems = list(problems)
    derived = derive(problems, solutions, readings)
    return [problem.model_copy(update={"techniques": derived[problem.id]}) for problem in problems]
