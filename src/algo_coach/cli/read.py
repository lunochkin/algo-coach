import argparse
import sys
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.classifier import EFFORT, MODEL
from algo_coach.cli.transport import transport
from algo_coach.problems import ProblemStore
from algo_coach.readings import Progress, ReadingLog, read_corpus
from algo_coach.runs import ABORT_AFTER
from algo_coach.solutions import SolutionLog


def read(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    api = transport(args, parser)
    titles = {problem.id: problem.title for problem in ProblemStore(root).all()}

    def show(progress: Progress) -> None:
        """One line per canonical, on stderr and flushed: a call takes seconds."""
        counter = f"[{progress.index:>{len(str(progress.total))}}/{progress.total}]"
        if progress.reason is not None:
            verdict = f"! {progress.reason}"
        else:
            verdict = " ".join(progress.techniques) or "— no technique"
        title = titles.get(progress.problem_id, progress.problem_id)
        print(f"{counter} {title[:40]:<40}  {verdict}", file=sys.stderr, flush=True)

    result = read_corpus(
        api,
        ReadingLog(root),
        CallLog(root),
        SolutionLog(root).solutions(),
        limit=args.limit,
        concurrency=args.concurrency,
        fresh=args.fresh,
        on_progress=show,
    )

    print(f"{result.read} canonical(s) read by {MODEL}, effort {EFFORT}")
    if result.undecided:
        print(f"{result.undecided} named no technique")
    if result.aborted:
        parser.exit(1, f"read: aborted after {ABORT_AFTER} consecutive failures\n")
    if result.failed and not result.written:
        parser.exit(1, "read: nothing landed\n")
