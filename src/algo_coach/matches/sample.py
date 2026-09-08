"""The order user matches are asked for, levelled per template rather than
per card: a form no user match covers is a gap no card-level count reports."""

import random
from collections import Counter
from collections.abc import Iterable, Sequence

from algo_coach.matches.matcher import candidates
from algo_coach.matches.questions import Question, questions
from algo_coach.schema import Card, MatchSource, Problem, Solution, TemplateMatch


def unsettled(
    cards: Iterable[Card],
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    matches: Iterable[TemplateMatch],
    *,
    card: str | None = None,
    seed: int = 0,
) -> list[Question]:
    """The questions a user match would settle something about, in the order to
    ask them. `card` narrows the pool to one. A machine verdict does not take a
    question out of it: a machine match is what the user's match is scored
    against."""
    asking = [
        question
        for question in questions(cards, problems, solutions)
        if card is None or question.card.slug == card
    ]
    user = {
        (match.template_id, match.solution_id)
        for match in matches
        if match.source is MatchSource.USER
    }
    return spread(
        [question for question in asking if not settled(question, user)],
        # Every user record, not only those on what is being asked: the counts
        # say what the reference already covers.
        covered=Counter(match.template_id for match in matches if match.source is MatchSource.USER),
        seed=seed,
    )


def settled(question: Question, user: set[tuple[str, str]]) -> bool:
    """Whether the user has answered every candidate of this card for this
    solution."""
    return all(
        (template.id, question.solution.id) in user for template in candidates(question.card)
    )


def spread(asking: Sequence[Question], *, covered: Counter[str], seed: int = 0) -> list[Question]:
    """The pool ordered so no single card's forms carry the reference: each
    step takes from the card whose template has the fewest user matches, so any
    prefix is spread. Shuffled within a card by `seed`."""
    pool = list(asking)
    random.Random(seed).shuffle(pool)

    queues: dict[str, list[Question]] = {}
    forms: dict[str, list[str]] = {}
    for question in pool:
        # Keyed by slug, not by the minted id, which differs per store: a tie
        # on coverage breaks on this key.
        queues.setdefault(question.card.slug, []).append(question)
        forms[question.card.slug] = [template.id for template in candidates(question.card)]

    counts = Counter(covered)
    order: list[Question] = []
    while queues:
        # Sorted, so the slug breaks a tie on coverage.
        drawn = min(
            sorted(queues),
            key=lambda slug: min(counts[form] for form in forms[slug]),
        )
        order.append(queues[drawn].pop())
        counts.update(forms[drawn])
        if not queues[drawn]:
            del queues[drawn]
    return order
