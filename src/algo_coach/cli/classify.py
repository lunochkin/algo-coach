import argparse
from pathlib import Path

from algo_coach.claims import MODEL, PROMPT_VERSION, classify_backlog
from algo_coach.claims.run import ABORT_AFTER
from algo_coach.cli.client import client
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore


def classify(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """Claim the backlog."""
    api = client(args, parser)
    log = AttemptLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
    result = classify_backlog(
        api,
        log,
        problems,
        user_id=args.user,
        limit=args.limit,
        technique=args.technique,
        redo=args.redo,
    )

    print(f"{result.classified} claim(s) written by {MODEL}, prompt {PROMPT_VERSION}")
    if result.redone:
        print(f"{result.redone} stale machine claim(s) re-derived")
    if result.undecided:
        print(f"{result.undecided} named no candidate — the fallback stands")
    for failure in result.failed:
        print(f"{failure.attempt_id}: {failure.reason}")
    if result.aborted:
        # Nonzero even when claims landed: the backlog was left unfinished for
        # a reason nothing in it can fix.
        parser.exit(1, f"classify: aborted after {ABORT_AFTER} consecutive failures\n")
    if result.failed and not result.written:
        parser.exit(1, "classify: nothing landed\n")
