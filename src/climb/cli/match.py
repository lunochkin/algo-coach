import argparse

from climb.calls import CallLog
from climb.cards import CardStore
from climb.cli.display import clipped, exit_on, named, progress
from climb.cli.transport import transport
from climb.matches import EFFORT, MODEL, MatchLog, Progress, match_corpus
from climb.solution_claims import load_problems
from climb.solutions import SolutionLog
from climb.storage import Database


def match(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Database) -> None:
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
