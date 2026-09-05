import argparse
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.classifier import EFFORT, MODEL
from algo_coach.cli.display import clipped, exit_on, named, progress
from algo_coach.cli.transport import transport
from algo_coach.problems import ProblemStore
from algo_coach.readings import Progress, ReadingLog, read_corpus
from algo_coach.solutions import SolutionLog


def read(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    api = transport(args, parser)
    titles = {problem.id: problem.title for problem in ProblemStore(root).all()}

    def show(one: Progress) -> None:
        progress(
            one.index,
            one.total,
            clipped(titles.get(one.problem_id, one.problem_id), 40),
            verdict=named(one.reason, one.techniques, none="no technique"),
        )

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
    exit_on(parser, "read", result)
