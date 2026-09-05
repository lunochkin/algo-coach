import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.claims import score_backlog
from algo_coach.claims.reading import Plan
from algo_coach.claims.run import Progress
from algo_coach.classifier import DEFAULT
from algo_coach.cli.display import chosen
from algo_coach.cli.scoring import alone, compared, failures, labels
from algo_coach.cli.status import Status
from algo_coach.cli.transport import transport
from algo_coach.log import AttemptLog
from algo_coach.readings import load_problems
from algo_coach.runs import ABORT_AFTER
from algo_coach.schema import Configuration


def configurations(
    args: argparse.Namespace, parser: argparse.ArgumentParser
) -> tuple[Configuration, ...]:
    """The rows `--model` opened, over the built-in classifier."""
    named = getattr(args, "named", None)
    if not named:
        return (DEFAULT,)
    unpinned = [model for model, _, provider, _ in named if not provider and model != DEFAULT.model]
    if unpinned:
        # Not defaulted to the built-in pin: an endpoint carries some models
        # and not others.
        parser.exit(2, f"score: --provider needed for {', '.join(sorted(set(unpinned)))}\n")
    built = tuple(
        Configuration(
            model=model,
            effort=effort or DEFAULT.effort,
            pin=provider or DEFAULT.pin,
            # Unlike the provider, part of what identifies a reading: a model
            # named without one runs at the built-in temperature.
            temperature=chosen(temperature, parser, command="score", fallback=DEFAULT.temperature),
        )
        for model, effort, provider, temperature in named
    )
    if len(set(built)) != len(built):
        # Twice would measure sampling noise, which nothing here consumes yet.
        parser.exit(2, "score: the same configuration named twice\n")
    return built


def score(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    if args.stored and args.limit is not None:
        parser.exit(2, "score: --stored with --limit — a cap on a run that pays for nothing\n")
    named = configurations(args, parser)

    # Before the transport, so a wait lands on the row it holds.
    board = Status(sys.stderr, named)
    # No credentials asked of a run that makes no call.
    api = None if args.stored else transport(args, parser, on_retry=board.waiting)
    log = AttemptLog(root)
    calls = CallLog(root)
    problems = {problem.id: problem for problem in load_problems(root)}

    def planned(plans: Sequence[Plan]) -> None:
        board.planned([len(plan.asking) for plan in plans])

    def answered(configuration: Configuration, progress: Progress) -> None:
        board.answered(configuration, failed=progress.reason is not None)

    try:
        result = score_backlog(
            api,
            log,
            calls,
            problems,
            user_id=args.user,
            configurations=named,
            concurrency=args.concurrency,
            fresh=args.fresh,
            limit=0 if args.stored else args.limit,
            on_plan=planned,
            on_progress=answered,
        )
    finally:
        # In a `finally`, so a run that raised leaves a whole block.
        board.close()

    if not result.eval_set:
        parser.exit(1, f"score: nothing hand-claimed to score against for {args.user}\n")
    aborted = [
        name
        for name, scored in zip(labels(named), result.scores, strict=True)
        if scored.score.aborted
    ]
    if aborted:
        # The numbers are withheld, the reasons are not: a share over the
        # slice read before the break would be taken for the whole answer.
        for name, scored in zip(labels(named), result.scores, strict=True):
            if scored.score.failed:
                print(failures(name, scored.score), file=sys.stderr)
        parser.exit(
            1,
            f"\nscore: {', '.join(aborted)} aborted after {ABORT_AFTER} consecutive failures\n",
        )
    if not result.common:
        # Apart from the abort above: ground truth exists, no reading of it
        # does.
        parser.exit(1, "score: nothing every configuration named has read\n")

    if len(result.scores) == 1:
        alone(result)
    else:
        compared(result, splits=args.splits)
