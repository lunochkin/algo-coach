"""The hand annotation: which of a card's forms a solution displays.

The question is the card and the record is the pair. One statement is read
once and judged against every form of the card, and the answer writes a row per
template. The ones the solution does not display are included: a reference that
only named matches would score the matcher's "yes" and say nothing about its
"no".

Blind by default. The first pass is where the line gets drawn between
exercising a form and merely admitting it. An annotation made with a verdict in
view records what it reviewed rather than what it read, and `informed_by` names
the calls it saw.

The prompt is a two-pane screen rather than a scroll, and `annotating.py` holds
it. What is asked and what is written stay here, so a sitting can be driven
without a terminal.
"""

import argparse
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from algo_coach.cards import CardStore
from algo_coach.cli.annotating import Annotating
from algo_coach.matches import MatchLog, Question, annotatable, candidates
from algo_coach.mint import user_match
from algo_coach.problems import ProblemStore
from algo_coach.schema import MatchSource, Template, TemplateMatch
from algo_coach.solutions import SolutionLog


class Landing:
    """What one answer writes: every pair of the card, positive and negative.

    Held apart from the prompt so a sitting cut short keeps what was answered.
    The log is append-only, and each question is a whole write.
    """

    def __init__(self, log: MatchLog, read: Mapping[tuple[str, str], TemplateMatch]):
        self.log = log
        self.read = read
        self.written = 0

    def __call__(self, question: Question, picked: set[str]) -> None:
        forms = candidates(question.card)
        saw = shown(question, forms, self.read)
        for form in forms:
            self.log.append(
                user_match(
                    form.id,
                    question.solution.id,
                    matched=form.id in picked,
                    informed_by=saw,
                )
            )
            self.written += 1


def annotating(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> Annotating:
    """The sitting, built but not run.

    What the matcher is scored against, so it writes `MatchSource.USER` records
    carrying no configuration: nothing re-derives them, which is what makes
    them stand on read however early they were written.
    """
    cards = CardStore(root).all()
    if args.card and not any(card.slug == args.card for card in cards):
        parser.exit(2, f"annotate: no card {args.card!r} — seed it first\n")

    log = MatchLog(root)
    stored = log.matches()
    pool = annotatable(
        cards,
        ProblemStore(root).all(),
        SolutionLog(root).solutions(),
        stored,
        card=args.card,
        seed=args.seed,
    )
    if not pool:
        left = f"left to annotate for {args.card}" if args.card else "left to annotate"
        parser.exit(1, f"annotate: nothing {left}\n")

    read = machine_verdicts(stored) if args.verdict else {}
    return Annotating(pool[: args.count], read, Landing(log, read))


def annotate(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """The matcher's question, answered by hand over sampled canonicals."""
    app = annotating(args, parser, root)
    app.run()
    print(f"{app.count} question(s) annotated, {app.answered.written} record(s) written")


def machine_verdicts(matches: Iterable[TemplateMatch]) -> dict[tuple[str, str], TemplateMatch]:
    """The latest reading per pair, whatever configuration produced it.

    Every configuration's, not one named on the command line: this is shown to
    a reader rather than scored, and which matcher answered is printed beside
    the verdict. A pair the hand has settled is not among them — the reader is
    being shown what a machine read, not what they wrote.
    """
    latest: dict[tuple[str, str], TemplateMatch] = {}
    for match in matches:
        if match.source is not MatchSource.CLASSIFIER:
            continue
        pair = (match.template_id, match.solution_id)
        if pair not in latest or match.created_at >= latest[pair].created_at:
            latest[pair] = match
    return latest


def shown(
    question: Question,
    forms: Sequence[Template],
    read: Mapping[tuple[str, str], TemplateMatch],
) -> list[str]:
    """The calls whose verdicts the prompt put in front of the annotator.

    One call answers a whole card, so the forms of one question usually name
    the same one; it is listed once. A form no matcher has read showed nothing,
    so it informed nothing.

    Recorded on every pair the answer writes, positive and negative alike. What
    the reader saw is a fact about the sitting rather than about the verdict,
    and the negatives are scored as the positives are.
    """
    seen: list[str] = []
    for form in forms:
        match = read.get((form.id, question.solution.id))
        if match is not None and match.call_id is not None and match.call_id not in seen:
            seen.append(match.call_id)
    return seen
