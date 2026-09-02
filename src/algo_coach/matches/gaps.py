"""Which core templates the corpus displays, and which it cannot exercise. A
view over the standing matches, never stored."""

from collections.abc import Iterable

from pydantic import BaseModel

from algo_coach.matches.matcher import candidates
from algo_coach.matches.standing import standing_matches
from algo_coach.schema import (
    Card,
    Problem,
    ProblemStatus,
    Solution,
    SolutionRole,
    Template,
    TemplateMatch,
)


class Coverage(BaseModel):
    """One core template and the canonicals a standing verdict says display it.

    Carries the slugs rather than the ids alone: a report names the template a
    generation run is aimed at, and an id means nothing in another store.
    """

    card_slug: str
    template_id: str
    template_slug: str
    solution_ids: list[str]

    @property
    def gap(self) -> bool:
        return not self.solution_ids


def core(card: Card) -> list[Template]:
    """The templates a ladder must cover: what `candidates` asks about, less
    the capstone, which is surfaced on request alone."""
    return [template for template in candidates(card) if not template.optional]


def coverage(
    cards: Iterable[Card],
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    matches: Iterable[TemplateMatch],
) -> list[Coverage]:
    """Every core template, in the order its card authored it, with what
    displays it. A retired problem's canonicals count for nothing: they fill no
    rung, so a form only they display is still a gap."""
    served = {problem.id for problem in problems if problem.status is not ProblemStatus.RETIRED}
    displaying = {
        solution.id
        for solution in solutions
        if solution.role is SolutionRole.CANONICAL and solution.problem_id in served
    }
    found: dict[str, list[str]] = {}
    for (template_id, solution_id), match in standing_matches(matches).items():
        if match.matched and solution_id in displaying:
            found.setdefault(template_id, []).append(solution_id)
    return [
        Coverage(
            card_slug=card.slug,
            template_id=template.id,
            template_slug=template.slug,
            solution_ids=sorted(found.get(template.id, [])),
        )
        for card in cards
        for template in core(card)
    ]


def uncovered(covered: Iterable[Coverage]) -> list[Coverage]:
    """The core templates nothing displays. The card claims to teach each of
    them, so this is what the next generation run is aimed at."""
    return [one for one in covered if one.gap]
