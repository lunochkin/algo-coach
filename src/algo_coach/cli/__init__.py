"""The CLI: one adapter over the engine, one module per command."""

import argparse
import os
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

from dotenv import find_dotenv, load_dotenv

from algo_coach.classifier import DEFAULT
from algo_coach.cli.bench import SITES
from algo_coach.cli.board import board
from algo_coach.cli.claim import claim
from algo_coach.cli.claim_solutions import claim_solutions
from algo_coach.cli.classify import classify
from algo_coach.cli.gaps import gaps
from algo_coach.cli.generate import generate
from algo_coach.cli.hand_match import hand_match
from algo_coach.cli.match import match
from algo_coach.cli.movement import moved
from algo_coach.cli.problem import problem
from algo_coach.cli.rows import Rows
from algo_coach.cli.score import score
from algo_coach.cli.seed import BadLine, seed
from algo_coach.runs import CONCURRENCY

DATA_ROOT = Path("data")

# What a shell reports for a command its user stopped: 128 plus the signal.
INTERRUPTED = 130

# a parser or one of its groups: both take `add_argument`
Flags = argparse._ActionsContainer  # pyright: ignore[reportPrivateUsage]

__all__ = ["DATA_ROOT", "INTERRUPTED", "BadLine", "main"]


class _Defaults(argparse.ArgumentDefaultsHelpFormatter):
    """`None` and `False` are the absence of a flag, so no default is shown for
    them."""

    def _get_help_string(self, action: argparse.Action) -> str | None:
        if action.default is None or action.default is False:
            return action.help
        return super()._get_help_string(action)


def _command(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],  # pyright: ignore[reportPrivateUsage]
    name: str,
    help: str,
) -> argparse.ArgumentParser:
    return sub.add_parser(name, help=help, formatter_class=_Defaults)


def _user_argument(parser: Flags) -> None:
    parser.add_argument(
        "--user",
        default=os.environ.get("ALGO_COACH_USER", "local"),
        help="whose attempts to read; stands in for authentication",
    )


def _run_arguments(parser: Flags, *, record: str, question: str = "prompt", per: str = "") -> None:
    """The flags every run over a backlog takes."""
    parser.add_argument(
        "--concurrency",
        type=int,
        default=CONCURRENCY,
        help=f"calls in flight at once{per}; one at a time otherwise",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help=f"ask again even where a stored {record} answers the same {question}",
    )


SETTINGS = ("--model", "--effort", "--provider", "--temperature")


class RowKeywords(TypedDict):
    dest: str
    action: type[argparse.Action]
    opener: str
    fills: list[str]
    opens_by_default: str | None


def _rows(dest: str, opener: str, *, opens_by_default: str | None = None) -> RowKeywords:
    """The `add_argument` keywords that put a flag into the rows `opener`
    begins. One destination for all of them, so which setting followed which
    opener survives."""
    fills = [flag for flag in SETTINGS if flag != opener]
    return RowKeywords(
        dest=dest, action=Rows, opener=opener, fills=fills, opens_by_default=opens_by_default
    )


def _configuration_arguments(parser: Flags, rows: RowKeywords, opener: str, **help: str) -> None:
    """`--model`, `--effort`, `--provider` and `--temperature`, each filling the
    row the `opener` before it began. `help` overrides the wording of one flag,
    keyed by its name."""
    wording = {
        "model": f"the model writing the {opener} before it",
        "effort": f"the effort of the {opener} before it",
        "provider": f"the backend to pin the {opener} before it to",
        "temperature": f"what the {opener} before it samples at; 'default' for the provider's own",
    } | help
    for flag in SETTINGS:
        name = flag[2:]
        parser.add_argument(flag, metavar=name.upper(), help=wording[name], **rows)


def main() -> None:
    # Before the parser, since a default reads the environment too. An exported
    # variable wins over the file, and the file is found from the working
    # directory rather than from the installed package.
    load_dotenv(find_dotenv(usecwd=True))

    parser = argparse.ArgumentParser(prog="algo-coach")
    sub = parser.add_subparsers(dest="command", required=True)

    seed_parser = _command(sub, "seed", "seed authored content into the store")
    seed_parser.add_argument("kind", choices=["cards"])
    seed_parser.add_argument("source", help="path to an authored JSON file, or a directory of them")

    board_parser = _command(sub, "board", "per-technique progress, derived from the log")
    board_parser.add_argument("--json", action="store_true", help="emit rows instead of a table")
    board_parser.add_argument(
        "--stale", action="store_true", help="order by recency, least recently practised first"
    )
    _user_argument(board_parser)

    claim_parser = _command(sub, "claim", "name the techniques a piece of code used")
    subject = claim_parser.add_subparsers(dest="subject", required=True)
    attempts_parser = subject.add_parser(
        "attempts",
        help="the user's attempts: the classifier, or the user with --by-hand",
        formatter_class=_Defaults,
    )
    attempts_parser.add_argument(
        "--by-hand",
        action="store_true",
        help="ask the user, one attempt at a time; run the classifier otherwise",
    )
    attempts_parser.add_argument(
        "--technique", help="only attempts whose problem carries it; every technique otherwise"
    )
    _user_argument(attempts_parser)
    by_hand = attempts_parser.add_argument_group("with --by-hand")
    by_hand.add_argument("--count", type=int, default=10, help="how many to ask about")
    by_hand.add_argument("--lines", type=int, default=120, help="lines of code to show")
    by_hand.add_argument("--seed", type=int, default=0, help="sampling order")
    by_hand.add_argument(
        "--revise", action="store_true", help="ask again about attempts already claimed"
    )
    _configuration_arguments(
        by_hand,
        _rows("named", "--model", opens_by_default=DEFAULT.model),
        "--model",
        model="a classifier whose claim to show beside the user's; repeatable",
        provider="the endpoint the --model before it read from",
        temperature="what the --model before it sampled at; 'default' for the provider's own",
    )
    # Unset rather than 0: "not passed" has to be a state the flag cannot
    # also be given as a value.
    by_hand.add_argument(
        "--disputed",
        type=int,
        default=None,
        help="how many of them must read it differently; every claim otherwise",
    )
    classifier = attempts_parser.add_argument_group("without --by-hand")
    classifier.add_argument(
        "--limit", type=int, help="how many attempts to claim; the whole backlog otherwise"
    )
    classifier.add_argument(
        "--redo",
        action="store_true",
        help="also re-derive claims an older model or prompt version made",
    )
    _run_arguments(classifier, record="claim")

    solutions_parser = subject.add_parser(
        "solutions", help="the stored canonicals, by the classifier", formatter_class=_Defaults
    )
    solutions_parser.add_argument(
        "--limit", type=int, help="how many canonicals to claim; every unclaimed one otherwise"
    )
    _run_arguments(solutions_parser, record="claim")

    match_parser = _command(sub, "match", "which problems exercise a card's templates")
    match_parser.add_argument(
        "--by-hand",
        action="store_true",
        help="ask the user, one solution at a time; run the matcher otherwise",
    )
    match_parser.add_argument("--card", help="one card by slug; every seeded card otherwise")
    by_hand = match_parser.add_argument_group("with --by-hand")
    by_hand.add_argument("--count", type=int, default=10, help="how many to ask about")
    by_hand.add_argument("--seed", type=int, default=0, help="sampling order")
    by_hand.add_argument(
        "--verdict", action="store_true", help="show what the matcher read the same pairs as"
    )
    matcher = match_parser.add_argument_group("without --by-hand")
    matcher.add_argument(
        "--limit", type=int, help="how many pairs to read; every outstanding one otherwise"
    )
    _run_arguments(matcher, record="record", question="question")

    generate_parser = _command(sub, "generate", "write problems for one of a card's templates")
    generate_parser.add_argument("--card", help="the card, by slug; narrows --gaps to it")
    generate_parser.add_argument("--template", help="its template, by slug")
    generate_parser.add_argument(
        "--gaps",
        action="store_true",
        help="write for every core template carrying no match, rather than one named",
    )
    generate_parser.add_argument("--count", type=int, default=1, help="how many problems to write")
    generate_parser.add_argument(
        "--replay",
        action="store_true",
        help="re-ask the answering sites about the stored problems, writing nothing to the corpus",
    )
    generate_parser.add_argument(
        "--resume",
        action="store_true",
        help="carry every held draft forward, from the step its bench or its own state moved",
    )
    generate_parser.add_argument(
        "--drafts",
        action="store_true",
        help="list the stored drafts, naming the step each would resume at, without calling",
    )
    generate_parser.add_argument(
        "--all",
        action="store_true",
        help="with --drafts, list the rejected ones too; only what a sweep reaches otherwise",
    )
    generate_parser.add_argument(
        "--draft",
        metavar="ID",
        help="read one stored draft whole, by id or a prefix of one, without calling",
    )
    generate_parser.add_argument(
        "--limit", type=int, help="how many stored problems to replay; every one otherwise"
    )
    generate_parser.add_argument(
        "--fresh",
        action="store_true",
        help="replay a pair even where a record answers the same prompt",
    )
    sited = _rows("sites", "--site")
    generate_parser.add_argument(
        "--site",
        metavar="SITE",
        choices=SITES,
        help=f"the call site the settings after it configure: {', '.join(SITES)}; repeatable",
        **sited,
    )
    _configuration_arguments(generate_parser, sited, "--site")

    problem_parser = _command(sub, "problem", "read one stored problem, or list the corpus")
    problem_parser.add_argument(
        "id", nargs="?", help="the problem, by id or a prefix of one; every one otherwise"
    )

    gaps_parser = _command(sub, "gaps", "core templates no stored solution displays")
    gaps_parser.add_argument(
        "--all", action="store_true", help="every core template; only the gaps otherwise"
    )

    score_parser = _command(sub, "score", "the classifier against the user's own claims")
    score_parser.add_argument(
        "--limit",
        type=int,
        help="how many attempts to read per classifier; every unread one otherwise",
    )
    _configuration_arguments(
        score_parser,
        _rows("named", "--model", opens_by_default=DEFAULT.model),
        "--model",
        model="a classifier to score; repeatable",
    )
    score_parser.add_argument(
        "--stored",
        action="store_true",
        help="score only claims already stored, making no call",
    )
    score_parser.add_argument(
        "--splits",
        action="store_true",
        help="print the per-technique table and every attempt read differently; counted otherwise",
    )
    _run_arguments(score_parser, record="claim", per=" per model and endpoint")
    _user_argument(score_parser)

    movement_parser = _command(
        sub, "movement", "how far the classifier's claims move the board off the fallback"
    )
    _user_argument(movement_parser)

    args = parser.parse_args()
    # Read at call time, not at import: tests point DATA_ROOT elsewhere.
    root = DATA_ROOT
    try:
        dispatch(args, parser, root)
    except KeyboardInterrupt:
        # Not a fault: every command appends as it goes, so what landed is
        # kept and a traceback would name only where the user was.
        parser.exit(INTERRUPTED, "\ninterrupted\n")


# every command takes the parser, whether or not it exits through it
COMMANDS: dict[str, Callable[[argparse.Namespace, argparse.ArgumentParser, Path], None]] = {
    "seed": seed,
    "board": lambda args, _parser, root: board(args, root),
    # one command per record; the subject names the code, `--by-hand` the writer
    "claim": lambda args, parser, root: (
        claim_solutions if args.subject == "solutions" else claim if args.by_hand else classify
    )(args, parser, root),
    "problem": problem,
    "gaps": lambda args, _parser, root: gaps(args, root),
    "generate": generate,
    "match": lambda args, parser, root: (hand_match if args.by_hand else match)(args, parser, root),
    "score": score,
    "movement": moved,
}


def dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    COMMANDS[args.command](args, parser, root)
