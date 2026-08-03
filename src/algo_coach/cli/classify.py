import argparse
from pathlib import Path

from anthropic import Anthropic

from algo_coach.claims import MODEL, PROMPT_VERSION, classify_backlog
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore


def classify(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """Claim the backlog. The key comes from the environment, so nothing about
    the account reaches the store or this repo."""
    log = AttemptLog(root)
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
    result = classify_backlog(
        Anthropic(),
        log,
        problems,
        user_id=args.user,
        limit=args.limit,
        technique=args.technique,
    )

    print(f"{result.classified} claim(s) written by {MODEL}, prompt {PROMPT_VERSION}")
    if result.undecided:
        print(f"{result.undecided} named no candidate — the fallback stands")
    for failure in result.failed:
        print(f"{failure.attempt_id}: {failure.reason}")
    if result.failed and not result.classified:
        parser.exit(1, "classify: nothing landed\n")
