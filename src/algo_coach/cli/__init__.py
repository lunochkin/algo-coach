"""The CLI: one adapter over the engine, one module per command.

Commands take the data root rather than reaching for it, so `main` is the only
place that decides where the store lives.
"""

import argparse
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from algo_coach.claims import CONCURRENCY
from algo_coach.cli.board import board
from algo_coach.cli.claim import claim
from algo_coach.cli.classify import classify
from algo_coach.cli.drill import drill
from algo_coach.cli.match import match
from algo_coach.cli.movement import moved
from algo_coach.cli.push import BadLine, push
from algo_coach.cli.score import Named, score
from algo_coach.cli.seed import seed

DATA_ROOT = Path("data")

# What a shell reports for a command its user stopped: 128 plus the signal.
INTERRUPTED = 130

__all__ = ["BadLine", "DATA_ROOT", "INTERRUPTED", "main"]


class _Defaults(argparse.ArgumentDefaultsHelpFormatter):
    """Show a default only where there is one to show: `None` and `False` are
    the absence of a flag, not a value it carries."""

    def _get_help_string(self, action: argparse.Action) -> str | None:
        if action.default is None or action.default is False:
            return action.help
        return super()._get_help_string(action)


def _command(sub: argparse._SubParsersAction, name: str, help: str) -> argparse.ArgumentParser:
    return sub.add_parser(name, help=help, formatter_class=_Defaults)


def _user_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--user",
        default=os.environ.get("ALGO_COACH_USER", "local"),
        help="identity to stamp on ingested records; stands in for authentication",
    )


def main() -> None:
    # Before the parser, since a default reads the environment too. An exported
    # variable wins over the file: the shell is the deliberate one. Found from
    # the working directory, like the data root — not from the package, which
    # sits elsewhere once installed.
    load_dotenv(find_dotenv(usecwd=True))

    parser = argparse.ArgumentParser(prog="algo-coach")
    sub = parser.add_subparsers(dest="command", required=True)

    push_parser = _command(sub, "push", "ingest pushed records from JSONL")
    push_parser.add_argument("kind", choices=["attempts", "problems"])
    push_parser.add_argument("source", help="path to a JSONL file, or - for stdin")
    _user_argument(push_parser)

    seed_parser = _command(sub, "seed", "seed authored content into the store")
    seed_parser.add_argument("kind", choices=["cards"])
    seed_parser.add_argument("source", help="path to an authored JSON file, or a directory of them")

    board_parser = _command(sub, "board", "per-technique standing, derived from the log")
    board_parser.add_argument("--json", action="store_true", help="emit rows instead of a table")
    board_parser.add_argument(
        "--stale", action="store_true", help="order by recency, least recently practised first"
    )
    _user_argument(board_parser)

    claim_parser = _command(sub, "claim", "name the techniques a stored attempt used")
    claim_parser.add_argument("--count", type=int, default=30, help="how many to ask about")
    claim_parser.add_argument(
        "--technique", help="only attempts whose problem carries it; every technique otherwise"
    )
    claim_parser.add_argument("--lines", type=int, default=120, help="lines of code to show")
    claim_parser.add_argument("--seed", type=int, default=0, help="sampling order")
    # Revising asks about what the hand pass answered rather than what it did
    # not, and shows what each named classifier read the same code as.
    claim_parser.add_argument(
        "--revise", action="store_true", help="ask again about attempts already claimed"
    )
    claim_parser.add_argument(
        "--model",
        dest="named",
        action=Named,
        metavar="MODEL",
        help="a classifier whose reading to show beside the claim; repeatable",
    )
    claim_parser.add_argument(
        "--effort",
        dest="named",
        action=Named,
        metavar="EFFORT",
        help="the effort of the --model before it",
    )
    claim_parser.add_argument(
        "--provider",
        dest="named",
        action=Named,
        metavar="PROVIDER",
        help="the endpoint the --model before it read from",
    )
    claim_parser.add_argument(
        "--temperature",
        dest="named",
        action=Named,
        metavar="TEMPERATURE",
        help="what the --model before it sampled at; 'default' for the provider's own",
    )
    # Unset rather than 0, so "not passed" is a state instead of a value the
    # flag could also be given. Every claim by default: reviewing only what a
    # classifier contests corrects the hand claims in one direction.
    claim_parser.add_argument(
        "--disputed",
        type=int,
        default=None,
        help="how many of them must read it differently; every claim otherwise",
    )
    _user_argument(claim_parser)

    classify_parser = _command(sub, "classify", "claim stored attempts with the classifier")
    classify_parser.add_argument(
        "--limit", type=int, help="how many attempts to claim; the whole backlog otherwise"
    )
    classify_parser.add_argument(
        "--technique", help="only attempts whose problem carries it; every technique otherwise"
    )
    classify_parser.add_argument(
        "--redo",
        action="store_true",
        help="also re-derive claims an older model or prompt version made",
    )
    classify_parser.add_argument(
        "--concurrency",
        type=int,
        default=CONCURRENCY,
        help="calls in flight at once; one at a time otherwise",
    )
    classify_parser.add_argument(
        "--fresh",
        action="store_true",
        help="ask again even where a stored claim answers the same prompt",
    )
    _user_argument(classify_parser)

    match_parser = _command(sub, "match", "which problems exercise a card's templates")
    match_parser.add_argument(
        "--limit", type=int, help="how many pairs to read; every outstanding one otherwise"
    )
    match_parser.add_argument("--card", help="one card by slug; every seeded card otherwise")
    match_parser.add_argument(
        "--concurrency",
        type=int,
        default=CONCURRENCY,
        help="calls in flight at once; one at a time otherwise",
    )
    match_parser.add_argument(
        "--fresh",
        action="store_true",
        help="ask again even where a stored record answers the same question",
    )

    score_parser = _command(sub, "score", "the classifier against the user's own claims")
    score_parser.add_argument(
        "--limit",
        type=int,
        help="how many attempts to read per classifier; every unread one otherwise",
    )
    # One destination for all of them, so which setting followed which model
    # survives. Named more than once, they are scored side
    # by side over what all of them read; named not at all, the built-in
    # classifier is the one scored.
    score_parser.add_argument(
        "--model",
        dest="named",
        action=Named,
        metavar="MODEL",
        help="a classifier to score; repeatable",
    )
    score_parser.add_argument(
        "--effort",
        dest="named",
        action=Named,
        metavar="EFFORT",
        help="the effort of the --model before it",
    )
    score_parser.add_argument(
        "--provider",
        dest="named",
        action=Named,
        metavar="PROVIDER",
        help="the backend to pin the --model before it to",
    )
    score_parser.add_argument(
        "--temperature",
        dest="named",
        action=Named,
        metavar="TEMPERATURE",
        help="what the --model before it samples at; 'default' for the provider's own",
    )
    score_parser.add_argument(
        "--stored",
        action="store_true",
        help="score only readings already stored, making no call",
    )
    score_parser.add_argument(
        "--concurrency",
        type=int,
        default=CONCURRENCY,
        help="calls in flight at once; one at a time otherwise",
    )
    score_parser.add_argument(
        "--fresh",
        action="store_true",
        help="ask again even where a stored claim answers the same prompt",
    )
    _user_argument(score_parser)

    movement_parser = _command(
        sub, "movement", "how far the classifier's claims move the board off the tags"
    )
    _user_argument(movement_parser)

    drill_parser = _command(sub, "drill", "pick a technique, then a problem for it")
    drill_parser.add_argument(
        "--technique", help="skip the first prompt with a known code; asked for otherwise"
    )
    drill_parser.add_argument(
        "--limit", type=int, default=10, help="how many choices to offer at each step"
    )
    _user_argument(drill_parser)

    args = parser.parse_args()
    # Read at call time, not at import: tests point DATA_ROOT elsewhere.
    root = DATA_ROOT
    try:
        dispatch(args, parser, root)
    except KeyboardInterrupt:
        # Ctrl-C is an answer, not a fault: every command appends as it goes,
        # so what landed is kept. A traceback would name the line the prompt
        # was waiting on — where the user was, not what went wrong.
        parser.exit(INTERRUPTED, "\ninterrupted\n")


def dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    if args.command == "seed":
        seed(args, parser, root)
    elif args.command == "board":
        board(args, root)
    elif args.command == "claim":
        claim(args, parser, root)
    elif args.command == "classify":
        classify(args, parser, root)
    elif args.command == "match":
        match(args, parser, root)
    elif args.command == "score":
        score(args, parser, root)
    elif args.command == "movement":
        moved(args, parser, root)
    elif args.command == "drill":
        drill(args, parser, root)
    else:
        push(args, parser, root)
