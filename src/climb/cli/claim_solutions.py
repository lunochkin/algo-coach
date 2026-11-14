import argparse

from climb.calls import CallLog
from climb.classifier import EFFORT, MODEL
from climb.cli.display import clipped, exit_on, named, progress
from climb.cli.transport import transport
from climb.problems import ProblemStore
from climb.solution_claims import Progress, SolutionClaimLog, read_corpus
from climb.solutions import SolutionLog
from climb.storage import Database


def claim_solutions(
    args: argparse.Namespace, parser: argparse.ArgumentParser, root: Database
) -> None:
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
        SolutionClaimLog(root),
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
    exit_on(parser, "claim", result)
