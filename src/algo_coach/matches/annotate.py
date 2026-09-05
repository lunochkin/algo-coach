"""A hand annotation: which of a card's forms one solution displays."""

from collections.abc import Iterable, Sequence

from algo_coach.matches.matcher import candidates
from algo_coach.matches.questions import Question
from algo_coach.matches.store import MatchLog
from algo_coach.mint import user_match


def annotate(
    log: MatchLog, question: Question, picked: Iterable[str], *, informed_by: Sequence[str] = ()
) -> int:
    """One record per candidate template, the picked ones positive and the
    rest negative, as `content.md` gives. Returns how many were written."""
    chosen = set(picked)
    forms = candidates(question.card)
    for form in forms:
        log.append(
            user_match(
                form.id, question.solution.id, matched=form.id in chosen, informed_by=informed_by
            )
        )
    return len(forms)


__all__ = ["annotate"]
