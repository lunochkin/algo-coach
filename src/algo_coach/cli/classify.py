import argparse
from pathlib import Path

from algo_coach.calls import CallLog
from algo_coach.claims import classify_backlog
from algo_coach.claims.run import Progress
from algo_coach.classifier import EFFORT, MODEL
from algo_coach.cli.display import clipped, exit_on, named, progress
from algo_coach.cli.transport import transport
from algo_coach.log import AttemptLog
from algo_coach.readings import load_problems


def classify(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    api = transport(args, parser)
    log = AttemptLog(root)
    calls = CallLog(root)
    problems = {problem.id: problem for problem in load_problems(root)}
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
    exit_on(parser, "classify", result)


def show(one: Progress) -> None:
    progress(
        one.index,
        one.total,
        clipped(one.title, 40),
        verdict=named(one.reason, one.techniques, none="no candidate"),
    )
