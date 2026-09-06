"""`match --by-hand`: which of a card's forms a solution displays. What is
asked and written stays here; `hand_matching.py` holds the two-pane prompt."""

import argparse
from collections.abc import Mapping, Sequence
from pathlib import Path

from algo_coach.cards import CardStore
from algo_coach.cli.hand_matching import HandMatching
from algo_coach.matches import MatchLog, Question, candidates, latest_readings, unsettled
from algo_coach.matches import hand_match as recorded
from algo_coach.readings import load_problems
from algo_coach.schema import Template, TemplateMatch
from algo_coach.solutions import SolutionLog


class Landing:
    """Every pair of the card, positive and negative. Apart from the prompt, so
    a sitting cut short keeps what was answered."""

    def __init__(self, log: MatchLog, read: Mapping[tuple[str, str], TemplateMatch]):
        self.log = log
        self.read = read
        self.written = 0

    def __call__(self, question: Question, picked: set[str]) -> None:
        saw = shown(question, candidates(question.card), self.read)
        self.written += recorded(self.log, question, picked, informed_by=saw)


def hand_matching(
    args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path
) -> HandMatching:
    """The sitting, built but not run."""
    cards = CardStore(root).all()
    if args.card and not any(card.slug == args.card for card in cards):
        parser.exit(2, f"match: no card {args.card!r} — seed it first\n")

    log = MatchLog(root)
    stored = log.matches()
    pool = unsettled(
        cards,
        load_problems(root),
        SolutionLog(root).solutions(),
        stored,
        card=args.card,
        seed=args.seed,
    )
    if not pool:
        left = f"left to match by hand for {args.card}" if args.card else "left to match by hand"
        parser.exit(1, f"match: nothing {left}\n")

    read = latest_readings(stored) if args.verdict else {}
    return HandMatching(pool[: args.count], read, Landing(log, read))


def hand_match(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    app = hand_matching(args, parser, root)
    app.run()
    print(f"{app.count} question(s) matched by hand, {app.answered.written} record(s) written")


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
