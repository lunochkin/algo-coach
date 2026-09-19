"""The problems a card has the user solve, derived from the template matches
and the card's selector. A view, never stored: `content.md` gives why.

Starting a card is here too, since the start draws the probes the ladder is
not allowed to hold.
"""

from collections.abc import Iterable
from datetime import datetime

from pydantic import BaseModel

from algo_coach.board import candidates
from algo_coach.log import CardRunLog
from algo_coach.matches import coverage
from algo_coach.mint import card_run
from algo_coach.schema import Attempt, Card, CardRun, Problem, Solution, TemplateMatch

# how many probes a start draws. One until use says otherwise, which
# `flows.md` names as deferred
PROBES = 1


class Rung(BaseModel):
    """One problem on a ladder, with the templates its canonicals display.

    A rung the selector filled covers none. `required` is derived from what the
    rung covers rather than stored, and a rung covering the optional template
    beside a core one offers that form as the alternative approach.
    """

    problem: Problem
    templates: list[str]  # template ids, in the order the card authored them
    required: bool
    # folded from the attempts made since the run began, never marked on the
    # rung: a ladder re-derived under a moved corpus keeps what was solved
    solved: bool = False


class Gap(BaseModel):
    """A core template no solution displays, named as the card names it.

    The card claims to teach the form, so the ladder reports the gap rather
    than substituting another problem for the rung. The next generation run is
    aimed at what this names.
    """

    template_id: str
    slug: str
    title: str


class Ladder(BaseModel):
    """What studying one card has the user solve."""

    card_slug: str
    rungs: list[Rung]
    gaps: list[Gap]


def ladder(
    card: Card,
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    matches: Iterable[TemplateMatch],
    attempts: Iterable[Attempt],
    *,
    since: datetime | None = None,
) -> Ladder:
    """A rung per template the corpus covers, then the selector's fill.

    The covering rungs come first, in the order the card authored its
    templates, and the fill follows least recently attempted first. A retired
    problem fills no rung, here and in `coverage`. `since` is when the card's
    run began, and a rung is solved by an attempt finished after it: having
    solved the problem once is not having studied the form.
    """
    problems = list(problems)
    attempts = list(attempts)
    done = _solved(attempts, since)
    answers = {solution.id: solution.problem_id for solution in solutions}
    offered = _offered(card, problems, attempts)
    rank = {problem.id: place for place, problem in enumerate(offered)}
    by_id = {problem.id: problem for problem in problems if problem.served}

    covering: dict[str, list[str]] = {}
    gaps: list[Gap] = []
    titles = {template.id: template.title for template in card.templates}
    core = {template.id for template in card.templates if not template.optional}
    for covered in coverage([card], problems, solutions, matches):
        filling = sorted(
            {answers[one] for one in covered.solution_ids if answers.get(one) in by_id},
            key=lambda id: (rank.get(id, len(rank)), id),
        )
        if not filling:
            if covered.gap:
                gaps.append(
                    Gap(
                        template_id=covered.template_id,
                        slug=covered.template_slug,
                        title=titles[covered.template_id],
                    )
                )
            continue
        covering.setdefault(filling[0], []).append(covered.template_id)

    rungs = [
        Rung(
            problem=by_id[id],
            templates=templates,
            required=bool(core & set(templates)),
            solved=id in done,
        )
        for id, templates in covering.items()
    ]
    # out to `size`, and never past a core template the corpus does not cover
    fill = [one for one in offered if one.id not in covering]
    rungs += [
        Rung(problem=one, templates=[], required=False, solved=one.id in done)
        for one in fill[: max(0, card.selector.size - len(rungs))]
    ]
    return Ladder(card_slug=card.slug, rungs=rungs, gaps=gaps)


def _solved(attempts: Iterable[Attempt], since: datetime | None) -> set[str]:
    """The problems solved since the run began. No run measures nothing, since
    the ladder is measured from the start."""
    if since is None:
        return set()
    return {
        attempt.problem_id
        for attempt in attempts
        if attempt.solved and attempt.finished_at >= since
    }


def _offered(card: Card, problems: Iterable[Problem], attempts: Iterable[Attempt]) -> list[Problem]:
    """The selector's problems, least recently attempted first, as a
    technique's candidates are ordered."""
    wanted = set(card.selector.difficulty)
    return [
        row.problem
        for row in candidates(card.selector.technique, problems, attempts)
        if not wanted or row.problem.difficulty in wanted
    ]


def start(
    runs: CardRunLog,
    card: Card,
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    matches: Iterable[TemplateMatch],
    attempts: Iterable[Attempt],
    *,
    user_id: str,
) -> CardRun:
    """The run a start mints, with the probes drawn in the same act.

    The ladder is measured from the start, so a run reaches the store carrying
    what the start drew. A card already started is returned rather than started
    again: `flows.md` leaves a second run deferred.
    """
    open_already = runs.started(user_id, card.id)
    if open_already is not None:
        return open_already
    problems, attempts = list(problems), list(attempts)
    resolved = ladder(card, problems, solutions, matches, attempts)
    run = card_run(user_id, card.id, probes(card, resolved, problems, attempts))
    runs.append(run)
    return run


def probes(
    card: Card,
    resolved: Ladder,
    problems: Iterable[Problem],
    attempts: Iterable[Attempt],
    count: int = PROBES,
) -> list[str]:
    """The problems a start offers as probes: the card's technique, unseen
    first, then least recently attempted, and never one the ladder holds.

    The whole technique rather than the selector's own filters. The filters
    narrow what the ladder teaches, and a probe asks whether the technique is
    recognised at all.
    """
    attempts = list(attempts)
    taught = {rung.problem.id for rung in resolved.rungs}
    seen = {attempt.problem_id for attempt in attempts}
    offered = [
        row.problem.id
        for row in candidates(card.selector.technique, problems, attempts)
        if row.problem.id not in taught
    ]
    return sorted(offered, key=lambda id: id in seen)[:count]
