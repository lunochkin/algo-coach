import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from algo_coach.board import TechniqueRow, per_technique, ungrouped
from algo_coach.claims import standing_claims
from algo_coach.cli.display import age
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.problems import load_problems


def board(args: argparse.Namespace, root: Path) -> None:
    log = AttemptLog(root)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    # Every problem, not the user's: an attempt names a minted id, and a
    # narrower index would miss a legitimate one.
    problems = {problem.id: problem for problem in load_problems(root)}
    claims = standing_claims(log.claims())
    labels = latest_by_attempt(log.self_labels())
    rows = per_technique(attempts, problems, claims, labels)
    if args.stale:
        rows.sort(key=lambda row: row.last_attempt_at)
    missed = len(ungrouped(attempts, problems, claims))

    if args.json:
        payload = {"rows": [row.model_dump(mode="json") for row in rows], "ungrouped": missed}
        print(json.dumps(payload, indent=2))
        return

    if not rows:
        print(f"no attempts for {args.user}")
        return

    print(render(rows, datetime.now(UTC)))
    if missed:
        noun = "attempt" if missed == 1 else "attempts"
        print(f"\n{missed} {noun} grouped nowhere — no technique resolved")


def render(rows: list[TechniqueRow], now: datetime) -> str:
    header = ("technique", "attempts", "solved", "last", "labels")
    body = [
        (
            row.technique,
            str(row.attempt_count),
            f"{row.solved_count}/{row.attempt_count}",
            age(row.last_attempt_at, now),
            " ".join(f"{mode}:{count}" for mode, count in sorted(row.self_labels.items())),
        )
        for row in rows
    ]
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )
