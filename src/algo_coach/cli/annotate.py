"""The hand annotation: which of a card's forms a solution displays. What is
asked and written stays here; `annotating.py` holds the two-pane prompt."""

import argparse
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from algo_coach.cards import CardStore
from algo_coach.cli.annotating import Annotating
from algo_coach.matches import MatchLog, Question, annotatable, candidates
from algo_coach.matches import annotate as annotated
from algo_coach.readings import load_problems
from algo_coach.schema import MatchSource, Template, TemplateMatch
from algo_coach.solutions import SolutionLog
from algo_coach.standing import latest_by


class Landing:
    """Every pair of the card, positive and negative. Apart from the prompt, so
    a sitting cut short keeps what was answered."""

    def __init__(self, log: MatchLog, read: Mapping[tuple[str, str], TemplateMatch]):
        self.log = log
        self.read = read
        self.written = 0

    def __call__(self, question: Question, picked: set[str]) -> None:
        saw = shown(question, candidates(question.card), self.read)
        self.written += annotated(self.log, question, picked, informed_by=saw)


def annotating(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> Annotating:
    """The sitting, built but not run."""
    cards = CardStore(root).all()
    if args.card and not any(card.slug == args.card for card in cards):
        parser.exit(2, f"annotate: no card {args.card!r} — seed it first\n")

    log = MatchLog(root)
    stored = log.matches()
    pool = annotatable(
        cards,
        load_problems(root),
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
    app = annotating(args, parser, root)
    app.run()
    print(f"{app.count} question(s) annotated, {app.answered.written} record(s) written")


def machine_verdicts(matches: Iterable[TemplateMatch]) -> dict[tuple[str, str], TemplateMatch]:
    """The latest reading per pair, from any configuration: this is shown to a
    reader rather than scored."""
    return latest_by(
        (match for match in matches if match.source is MatchSource.CLASSIFIER),
        lambda match: (match.template_id, match.solution_id),
    )


def shown(
    question: Question,
    forms: Sequence[Template],
    read: Mapping[tuple[str, str], TemplateMatch],
) -> list[str]:
    """The calls whose verdicts the prompt showed. One call answers a whole
    card, so it is listed once."""
    seen: list[str] = []
    for form in forms:
        match = read.get((form.id, question.solution.id))
        if match is not None and match.call_id is not None and match.call_id not in seen:
            seen.append(match.call_id)
    return seen
