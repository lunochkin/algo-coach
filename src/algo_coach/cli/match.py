import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.cards import CardStore
from algo_coach.cli.transport import transport
from algo_coach.matches import EFFORT, MODEL, MatchLog, Progress, match_corpus
from algo_coach.problems import load_problems
from algo_coach.runs import ABORT_AFTER
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
    if result.aborted:
        parser.exit(1, f"match: aborted after {ABORT_AFTER} consecutive failures\n")
    if result.failed and not result.written:
        parser.exit(1, "match: nothing landed\n")


def show(progress: Progress) -> None:
    """One line per question, on stderr and flushed: a call takes seconds."""
    counter = f"[{progress.index:>{len(str(progress.total))}}/{progress.total}]"
    if progress.reason is not None:
        verdict = f"! {progress.reason}"
    else:
        verdict = " ".join(progress.templates) or "— no template"
    print(
        f"{counter} {progress.card_slug[:20]:<20} {progress.title[:40]:<40}  {verdict}",
        file=sys.stderr,
        flush=True,
    )
