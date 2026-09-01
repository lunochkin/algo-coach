"""Which solutions to ask about against which card, and what is already
settled.

A question is one card and one canonical — what a call carries. The record it
produces is per template and solution, and those are the pairs: independent of
each other, settled one at a time, and never asserted as a set. The question is
an economy of asking, so nothing but the call is keyed to it.

Pre-filtering is what makes the run affordable: a solution is offered only to
cards whose technique its problem carries, or the work is every template
against every solution for an answer that is almost always no.

References are never asked about. A reference is written to be plainly correct
rather than to display a form, so a verdict on one says nothing about what the
problem teaches.
"""

from collections.abc import Iterable, Mapping, Sequence

from pydantic import BaseModel

from algo_coach.matches.matcher import Configuration, candidates
from algo_coach.schema import (
    Card,
    MatchSource,
    Problem,
    Solution,
    SolutionRole,
    TemplateMatch,
)


class Question(BaseModel):
    """This canonical against this card's templates: the unit a call is made
    for, where a record is one template against one solution.

    The problem travels with it because the statement is context the code
    leaves implicit, and because its techniques are what offered the solution
    to this card.
    """

    card: Card
    problem: Problem
    solution: Solution

    @property
    def key(self) -> tuple[str, str]:
        return (self.card.id, self.solution.id)


def questions(
    cards: Iterable[Card], problems: Iterable[Problem], solutions: Iterable[Solution]
) -> list[Question]:
    """Every question worth a call, before what is already read is taken out.

    A card whose every template is a framing procedure asks nothing, so it
    produces no question rather than a call with no candidates.

    A solution whose problem is not stored asks nothing either. It cannot be
    offered to a card without the techniques that scope the offer, and the
    statement it was written against is not there to send.
    """
    asking = [card for card in cards if candidates(card)]
    by_id = {problem.id: problem for problem in problems}
    return [
        Question(card=card, problem=by_id[solution.problem_id], solution=solution)
        for solution in solutions
        if solution.role is SolutionRole.CANONICAL and solution.problem_id in by_id
        for card in asking
        if card.technique in by_id[solution.problem_id].techniques
    ]


def at_configuration(match: TemplateMatch, configuration: Configuration, prompt_hash: str) -> bool:
    """Whether this matcher, asked this question, produced the record.

    The same comparison staleness makes on a claim, and for the same reasons.
    The pin says which build answered and the temperature how it was sampled,
    while the provider that served it is recorded and never compared. A hand
    annotation is at no configuration at all, which keeps it out of what a
    re-run counts as answered. It is the reference a run is scored against, not
    a reading a run may rely on.
    """
    if match.source is not MatchSource.CLASSIFIER:
        return False
    return (match.model, match.effort, match.pin, match.temperature, match.prompt_hash) == (
        configuration.model,
        configuration.effort,
        configuration.pin,
        configuration.temperature,
        prompt_hash,
    )


def outstanding(
    asking: Sequence[Question],
    matches: Iterable[TemplateMatch],
    hashes: Mapping[tuple[str, str], str],
    *,
    configuration: Configuration,
) -> list[Question]:
    """The questions this configuration has not answered as it would ask them
    now.

    `hashes` is what each question would be sent, keyed by card and solution. A
    question stands while any of its pairs carries no record at that text — the
    rule readings already use, one level down. A pair already settled is
    re-answered by the call that goes out for the unsettled one beside it,
    which costs a verdict and settles nothing differently: the pairs are
    independent, and a later record on one supersedes only itself.
    """
    card_of = {
        template.id: question.card.id
        for question in asking
        for template in candidates(question.card)
    }
    read = {
        (match.template_id, match.solution_id)
        for match in matches
        if match.template_id in card_of
        and at_configuration(
            match, configuration, hashes.get((card_of[match.template_id], match.solution_id), "")
        )
    }
    return [
        question
        for question in asking
        if any(
            (template.id, question.solution.id) not in read
            for template in candidates(question.card)
        )
    ]
