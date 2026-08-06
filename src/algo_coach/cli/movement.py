import argparse
from pathlib import Path

from algo_coach.board import TechniqueMovement, movement
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore
from algo_coach.schema import ClaimSource
from algo_coach.techniques import standing_claims


def moved(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    """How far the classifier's claims move the board off the tag fallback.

    The classifier's only: a hand claim narrows for a different reason, and
    mixing the two would credit the machine with what the user decided.

    Standing ones only, and for the same reason: a machine claim on a
    hand-claimed attempt is a reading that never reaches the board, so counting
    it would report movement nothing moved.
    """
    log = AttemptLog(root)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    problems = {problem.id: problem for problem in ProblemStore(root).all()}
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
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )
