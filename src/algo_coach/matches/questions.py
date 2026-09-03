"""Which solutions to ask about against which card, and what is already settled."""

from collections.abc import Iterable, Mapping, Sequence

from pydantic import BaseModel

from algo_coach.calls import Configuration
from algo_coach.matches.matcher import candidates
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
    for, where a record is one template against one solution."""

    card: Card
    problem: Problem
    solution: Solution

    @property
    def key(self) -> tuple[str, str]:
        return (self.card.id, self.solution.id)


def questions(
    cards: Iterable[Card], problems: Iterable[Problem], solutions: Iterable[Solution]
) -> list[Question]:
    """Every question worth a call, before what is already read is taken out. A
    card of framing procedures alone and a solution whose problem is not stored
    both drop out: neither has anything to send."""
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
    """Whether this matcher, asked this question, produced the record. The
    provider that served it is recorded and never compared, and a hand
    annotation is at no configuration at all."""
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
    now. `hashes` is what each question would be sent, keyed by card and
    solution. A question stands while any of its pairs carries no record at
    that text, so a settled pair is re-answered by the call the unsettled one
    beside it needs."""
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
