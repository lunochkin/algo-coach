import argparse
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cli.display import clipped, exit_on, named, progress
from algo_coach.cli.transport import transport
from algo_coach.matches import EFFORT, MODEL, MatchLog, Progress, match_corpus
from algo_coach.readings import load_problems
from algo_coach.solutions import SolutionLog


def match(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    api = transport(args, parser)
    cards = CardStore(root).all()
    if args.card and not any(card.slug == args.card for card in cards):
        parser.exit(2, f"match: no card {args.card!r} — seed it first\n")

    result = match_corpus(
        api,
        MatchLog(root),
        CallLog(root),
        cards,
        load_problems(root),
        SolutionLog(root).solutions(),
        limit=args.limit,
        card_slug=args.card,
        concurrency=args.concurrency,
        fresh=args.fresh,
        on_progress=show,
    )

    print(f"{result.asked} card/solution question(s) read by {MODEL}, effort {EFFORT}")
    print(f"{result.matched} match(es), {result.unmatched} non-match(es) recorded")
    exit_on(parser, "match", result)


def show(one: Progress) -> None:
    progress(
        one.index,
        one.total,
        clipped(one.card_slug, 20),
        clipped(one.title, 40),
        verdict=named(one.reason, one.templates, none="no template"),
    )
