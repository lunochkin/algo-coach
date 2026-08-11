import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.claims import EFFORT, MODEL, classify_backlog
from algo_coach.claims.run import ABORT_AFTER, Progress
from algo_coach.cli.client import client
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore


def classify(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """Claim the backlog."""
    api = client(args, parser)
    log = AttemptLog(root)
    calls = CallLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
    result = classify_backlog(
        api,
        log,
        calls,
        problems,
        user_id=args.user,
        concurrency=args.concurrency,
        limit=args.limit,
        technique=args.technique,
        redo=args.redo,
        fresh=args.fresh,
        on_progress=show,
    )

    print(f"{result.classified} claim(s) written by {MODEL}, effort {EFFORT}")
    if result.redone:
        print(f"{result.redone} stale machine claim(s) re-derived")
    if result.undecided:
        print(f"{result.undecided} named no candidate — the fallback stands")
    # Each failure was reported by `show` as it happened; a second list here
    # would say it twice, and the counts are what stdout is for.
    if result.aborted:
        # Nonzero even when claims landed: the backlog was left unfinished for
        # a reason nothing in it can fix.
        parser.exit(1, f"classify: aborted after {ABORT_AFTER} consecutive failures\n")
    if result.failed and not result.written:
        parser.exit(1, "classify: nothing landed\n")


def show(progress: Progress) -> None:
    """A line per attempt, flushed: a call takes seconds, so a run that printed
    only at the end would look hung for minutes.

    To stderr, so the counts on stdout stay the command's output.
    """
    counter = f"[{progress.index:>{len(str(progress.total))}}/{progress.total}]"
    if progress.reason is not None:
        verdict = f"! {progress.reason}"
    else:
        verdict = " ".join(progress.techniques) or "— no candidate"
    print(f"{counter} {progress.title[:40]:<40}  {verdict}", file=sys.stderr, flush=True)
