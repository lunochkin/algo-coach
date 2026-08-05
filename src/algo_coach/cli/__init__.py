"""The CLI: one adapter over the engine, one module per command.

Commands take the data root rather than reaching for it, so `main` is the only
place that decides where the store lives.
"""

import argparse
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from algo_coach.cli.board import board
from algo_coach.cli.claim import claim
from algo_coach.cli.classify import classify
from algo_coach.cli.drill import drill
from algo_coach.cli.movement import moved
from algo_coach.cli.push import BadLine, push
from algo_coach.cli.score import score

DATA_ROOT = Path("data")

__all__ = ["BadLine", "DATA_ROOT", "main"]


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
    claim_parser.add_argument("--lines", type=int, default=60, help="lines of code to show")
    claim_parser.add_argument("--seed", type=int, default=0, help="sampling order")
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
    _user_argument(classify_parser)

    score_parser = _command(sub, "score", "the classifier against the user's own claims")
    score_parser.add_argument(
        "--limit", type=int, help="how many hand claims to score against; all of them otherwise"
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
    if args.command == "board":
        board(args, root)
    elif args.command == "claim":
        claim(args, parser, root)
    elif args.command == "classify":
        classify(args, parser, root)
    elif args.command == "score":
        score(args, parser, root)
    elif args.command == "movement":
        moved(args, parser, root)
    elif args.command == "drill":
        drill(args, parser, root)
    else:
        push(args, parser, root)
