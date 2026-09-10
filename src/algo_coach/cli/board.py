import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from algo_coach.attempt_claims import standing_attempt_claims
from algo_coach.board import TechniqueRow, excluded, per_technique, stalest_first, ungrouped
from algo_coach.cli.display import age, table
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.solution_claims import load_problems


def board(args: argparse.Namespace, root: Path) -> None:
    log = AttemptLog(root)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    # Every problem, not the user's: an attempt names a minted id, and a
    # narrower index would miss a legitimate one.
    problems = {problem.id: problem for problem in load_problems(root)}
    claims = standing_attempt_claims(log.claims())
    labels = latest_by_attempt(log.self_labels())
    rows = per_technique(attempts, problems, claims, labels)
    if args.stale:
        rows = stalest_first(rows, problems.values())
    missed = len(ungrouped(attempts, problems, claims))
    dropped = len(excluded(attempts, problems))

    if args.json:
        payload = {
            "rows": [row.model_dump(mode="json") for row in rows],
            "ungrouped": missed,
            "excluded": dropped,
        }
        print(json.dumps(payload, indent=2))
        return

    # a log holding only a defective problem's attempts still names them
    if not rows and not dropped:
        print(f"no attempts for {args.user}")
        return

    if rows:
        print(render(rows, datetime.now(UTC)))
    if missed:
        noun = "attempt" if missed == 1 else "attempts"
        print(f"\n{missed} {noun} grouped nowhere — no technique resolved")
    if dropped:
        noun = "attempt" if dropped == 1 else "attempts"
        print(f"\n{dropped} {noun} on a defective problem, not counted")


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
    return table(header, body)
