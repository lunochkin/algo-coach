import argparse

from climb.attempt_claims import classify_backlog
from climb.attempt_claims.run import Progress
from climb.calls import CallLog
from climb.classifier import EFFORT, MODEL
from climb.cli.display import clipped, exit_on, named, progress
from climb.cli.transport import transport
from climb.log import AttemptLog
from climb.solution_claims import load_problems
from climb.storage import Database


def classify(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Database) -> None:
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
    exit_on(parser, "claim", result)


def show(one: Progress) -> None:
    progress(
        one.index,
        one.total,
        clipped(one.title, 40),
        verdict=named(one.reason, one.techniques, none="no candidate"),
    )
