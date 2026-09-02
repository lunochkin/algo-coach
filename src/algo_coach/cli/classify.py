import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.claims import classify_backlog
from algo_coach.claims.run import ABORT_AFTER, Progress
from algo_coach.classifier import EFFORT, MODEL
from algo_coach.cli.transport import transport
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore


def classify(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    api = transport(args, parser)
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
    # Failures were named by `show` as they happened; only the counts here.
    if result.aborted:
        # Nonzero even when claims landed: the backlog was left unfinished.
        parser.exit(1, f"classify: aborted after {ABORT_AFTER} consecutive failures\n")
    if result.failed and not result.written:
        parser.exit(1, "classify: nothing landed\n")


def show(progress: Progress) -> None:
    """One line per attempt, on stderr and flushed: a call takes seconds."""
    counter = f"[{progress.index:>{len(str(progress.total))}}/{progress.total}]"
    if progress.reason is not None:
        verdict = f"! {progress.reason}"
    else:
        verdict = " ".join(progress.techniques) or "— no candidate"
    print(f"{counter} {progress.title[:40]:<40}  {verdict}", file=sys.stderr, flush=True)
