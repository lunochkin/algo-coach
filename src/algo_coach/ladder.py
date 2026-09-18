"""The problems a card has the user solve, derived from the template matches
and the card's selector. A view, never stored: `content.md` gives why."""

from collections.abc import Iterable

from pydantic import BaseModel

from algo_coach.board import candidates
from algo_coach.matches import coverage
from algo_coach.schema import Attempt, Card, Problem, Solution, TemplateMatch


class Rung(BaseModel):
    """One problem on a ladder, with the core templates its canonicals display.

    A rung the selector filled covers none, and requiredness is derived from
    what it covers rather than stored.
    """

    problem: Problem
    templates: list[str]  # template ids, in the order the card authored them


class Ladder(BaseModel):
    """What studying one card has the user solve."""

    card_slug: str
    rungs: list[Rung]
    # the core templates no solution displays, reported rather than substituted
    gaps: list[str]  # template slugs


def ladder(
    card: Card,
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    matches: Iterable[TemplateMatch],
    attempts: Iterable[Attempt],
) -> Ladder:
    """A rung per core template the corpus covers, then the selector's fill.

    The covering rungs come first, in the order the card authored its
    templates, and the fill follows least recently attempted first. A retired
    problem fills no rung, here and in `coverage`.
    """
    problems = list(problems)
    answers = {solution.id: solution.problem_id for solution in solutions}
    offered = _offered(card, problems, attempts)
    rank = {problem.id: place for place, problem in enumerate(offered)}
    by_id = {problem.id: problem for problem in problems if problem.served}

    covering: dict[str, list[str]] = {}
    gaps: list[str] = []
    for covered in coverage([card], problems, solutions, matches):
        filling = sorted(
            {answers[one] for one in covered.solution_ids if answers.get(one) in by_id},
            key=lambda id: (rank.get(id, len(rank)), id),
        )
        if not filling:
            gaps.append(covered.template_slug)
            continue
        covering.setdefault(filling[0], []).append(covered.template_id)

    rungs = [Rung(problem=by_id[id], templates=templates) for id, templates in covering.items()]
    # out to `size`, and never past a core template the corpus does not cover
    fill = [one for one in offered if one.id not in covering]
    rungs += [
        Rung(problem=one, templates=[]) for one in fill[: max(0, card.selector.size - len(rungs))]
    ]
    return Ladder(card_slug=card.slug, rungs=rungs, gaps=gaps)


def _offered(card: Card, problems: Iterable[Problem], attempts: Iterable[Attempt]) -> list[Problem]:
    """The selector's problems, least recently attempted first, as a
    technique's candidates are ordered."""
    wanted = set(card.selector.difficulty)
    return [
        row.problem
        for row in candidates(card.selector.technique, problems, attempts)
        if not wanted or row.problem.difficulty in wanted
    ]
