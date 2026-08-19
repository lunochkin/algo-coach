"""Which problems to test against which card, and what is already settled.

Pre-filtering is what makes the run affordable: a problem is offered only to
cards whose technique its tags reach, or the work is every template against
every problem for an answer that is almost always no.
"""

from collections.abc import Iterable, Mapping, Sequence

from pydantic import BaseModel

from algo_coach.matches.matcher import Configuration, candidates
from algo_coach.schema import Card, MatchSource, Problem, TemplateMatch


class Pair(BaseModel):
    """One question: this problem against this card's templates. The unit a
    call is made for, where the record is per template."""

    card: Card
    problem: Problem

    @property
    def key(self) -> tuple[str, str]:
        return (self.card.id, self.problem.id)


def pairs(cards: Iterable[Card], problems: Iterable[Problem]) -> list[Pair]:
    """Every pair worth a call, before what is already read is taken out.

    A card whose every template is a framing procedure asks nothing, so it
    produces no pair rather than a call with no candidates.
    """
    asking = [card for card in cards if candidates(card)]
    return [
        Pair(card=card, problem=problem)
        for problem in problems
        for card in asking
        if card.technique in problem.techniques
    ]


def at_configuration(match: TemplateMatch, configuration: Configuration, prompt_hash: str) -> bool:
    """Whether this matcher, asked this question, produced the record.

    The same comparison staleness makes on a claim, and for the same reasons:
    the pin says which build answered and the temperature how it was sampled,
    while the provider that served it is recorded and never compared. A hand
    annotation is at no configuration at all, which keeps it out of what a
    re-run counts as answered — it is the reference a run is scored against,
    not a reading a run may lean on.
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
    candidate_pairs: Sequence[Pair],
    matches: Iterable[TemplateMatch],
    hashes: Mapping[tuple[str, str], str],
    *,
    configuration: Configuration,
) -> list[Pair]:
    """The pairs this configuration has not answered at the question it would
    ask now.

    `hashes` is what each pair would be sent, keyed by card and problem. A
    pair is outstanding when any of its templates carries no record at that
    question — the rule readings already use, one level down: a template added
    to a card leaves the rest of that card's pairs unanswered by nothing more
    than the digest, and the call that reads the new form re-reads the others
    in the same breath.
    """
    card_of = {
        template.id: pair.card.id for pair in candidate_pairs for template in candidates(pair.card)
    }
    read = {
        (match.template_id, match.problem_id)
        for match in matches
        if match.template_id in card_of
        and at_configuration(
            match, configuration, hashes.get((card_of[match.template_id], match.problem_id), "")
        )
    }
    return [
        pair
        for pair in candidate_pairs
        if any((template.id, pair.problem.id) not in read for template in candidates(pair.card))
    ]
