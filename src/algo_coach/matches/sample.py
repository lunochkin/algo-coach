"""The order a hand annotation is asked in.

Levelled per template, not per card. The score is grouped per template and the
ladder resolves per template, so a form nothing has annotated is a gap no
card-level count reports. A re-seeded card gains such a form and stays the best
covered card there is, while holding the only gap in the set.

In the steady state the two agree. Annotating answers every template of a card
at once, so its counts move together, and the minimum over them is how many
times the card was asked about. They diverge exactly where those counts
diverge, which is the case worth having.
"""

import random
from collections import Counter
from collections.abc import Iterable, Sequence

from algo_coach.matches.matcher import candidates
from algo_coach.matches.questions import Question, questions
from algo_coach.schema import Card, MatchSource, Problem, Solution, TemplateMatch


def annotatable(
    cards: Iterable[Card],
    problems: Iterable[Problem],
    solutions: Iterable[Solution],
    matches: Iterable[TemplateMatch],
    *,
    card: str | None = None,
    seed: int = 0,
) -> list[Question]:
    """The questions a hand annotation would settle something about, in the
    order to ask them.

    Unannotated first and spread across templates, or the three cards on the
    technique the corpus holds most of carry the set. `card` narrows it to one,
    which is what annotating a card just added asks for; the order is the same
    rule either way.

    A machine verdict does not take a question out of the pool. It is what the
    annotation is scored against, so a run answering one settles nothing about
    whether a hand has.
    """
    asking = [
        question
        for question in questions(cards, problems, solutions)
        if card is None or question.card.slug == card
    ]
    hand = {
        (match.template_id, match.solution_id)
        for match in matches
        if match.source is MatchSource.USER
    }
    return spread(
        [question for question in asking if not settled(question, hand)],
        # Every hand record, not only those on what is being asked: the counts
        # say what the reference already covers, and narrowing to one card
        # would make its forms look untouched next to nothing.
        covered=Counter(match.template_id for match in matches if match.source is MatchSource.USER),
        seed=seed,
    )


def settled(question: Question, hand: set[tuple[str, str]]) -> bool:
    """Whether the hand has answered this whole card for this solution.

    Whole, because the question is the card: a partly annotated one is still
    worth asking, and the templates it already settled are re-answered by the
    same sitting at no cost. The rule the run path skips a pair by, one writer
    over.
    """
    return all(
        (template.id, question.solution.id) in hand for template in candidates(question.card)
    )


def spread(asking: Sequence[Question], *, covered: Counter[str], seed: int = 0) -> list[Question]:
    """The pool ordered so no single card's forms carry the reference.

    Each step takes a question from the card holding the least annotated
    template, so any prefix of the order is spread. A card is what a question
    carries and a template is what is counted: drawing one covers every
    candidate of that card, since the annotation answers all of them.

    Shuffled within a card by `seed`, so a sample is described by its seed
    rather than by listing what it held.
    """
    pool = list(asking)
    random.Random(seed).shuffle(pool)

    queues: dict[str, list[Question]] = {}
    forms: dict[str, list[str]] = {}
    for question in pool:
        # Keyed by slug, not by the minted id: a tie on coverage breaks on this
        # key, and an id minted per store would make the order differ between
        # two engines holding the same cards.
        queues.setdefault(question.card.slug, []).append(question)
        forms[question.card.slug] = [template.id for template in candidates(question.card)]

    counts = Counter(covered)
    order: list[Question] = []
    while queues:
        # Sorted, so the slug breaks a tie on coverage and the order is the
        # seed's alone.
        drawn = min(
            sorted(queues),
            key=lambda slug: min(counts[form] for form in forms[slug]),
        )
        order.append(queues[drawn].pop())
        counts.update(forms[drawn])
        if not queues[drawn]:
            del queues[drawn]
    return order
