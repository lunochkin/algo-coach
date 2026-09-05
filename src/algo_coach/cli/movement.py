import argparse
from pathlib import Path

from algo_coach.board import TechniqueMovement, movement
from algo_coach.claims import standing_claims
from algo_coach.cli.display import table
from algo_coach.log import AttemptLog
from algo_coach.readings import load_problems
from algo_coach.schema import ClaimSource


def moved(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    log = AttemptLog(root)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    problems = {problem.id: problem for problem in load_problems(root)}
    # Standing classifier claims only: a hand claim narrows for its own
    # reason, and a machine reading that never stands moved nothing.
    claims = {
        attempt_id: claim
        for attempt_id, claim in standing_claims(log.claims()).items()
        if claim.source is ClaimSource.CLASSIFIER
    }
    if not claims:
        parser.exit(1, f"movement: nothing classified for {args.user}\n")

    rows = movement(attempts, problems, claims)
    print(render(rows))
    print(f"\n{len(claims)} classifier claim(s); a row that barely moves was never declined")


def render(rows: list[TechniqueMovement]) -> str:
    header = ("technique", "fallback", "claimed", "moved")
    body = [(row.technique, str(row.fallback), str(row.claimed), f"{row.moved:+d}") for row in rows]
    return table(header, body)
