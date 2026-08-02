import argparse
import json
import os
import sys
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from algo_coach.board import TechniqueRow, per_technique, ungrouped
from algo_coach.ingest import ingest_attempts, ingest_problems
from algo_coach.log import AttemptLog, latest_by_attempt
from algo_coach.problems import ProblemStore

DATA_ROOT = Path("data")


class BadLine(Exception):
    """Not JSON at all: corrupt transport, not an invalid record. Ingest never
    sees it, so it cannot come back as a rejection."""


def _read_jsonl(source: str) -> Iterator[dict]:
    """One record per line, so a half-written file is still half-ingestible."""
    lines = sys.stdin if source == "-" else Path(source).read_text().splitlines()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            raise BadLine(f"line {number}: {exc.msg}") from exc


def _user_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--user",
        default=os.environ.get("ALGO_COACH_USER", "local"),
        help="identity to stamp on ingested records; stands in for authentication",
    )


def _push(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    records = _read_jsonl(args.source)
    try:
        if args.kind == "attempts":
            result = ingest_attempts(
                records,
                user_id=args.user,
                log=AttemptLog(DATA_ROOT),
                problems=ProblemStore(DATA_ROOT),
            )
        else:
            result = ingest_problems(records, user_id=args.user, store=ProblemStore(DATA_ROOT))
    except BadLine as exc:
        # Records before it are stored; re-pushing the fixed file is a no-op
        # on those, so resuming means running the command again.
        parser.exit(2, f"push: {exc}\n")

    print(result.model_dump_json(indent=2))
    if result.rejected:
        parser.exit(1)


def _board(args: argparse.Namespace) -> None:
    log = AttemptLog(DATA_ROOT)
    attempts = [attempt for attempt in log.attempts() if attempt.user_id == args.user]
    # Every problem, not the user's: an attempt resolves through the id it was
    # ingested with, and a narrower mapping would raise on a legitimate one.
    problems = {problem.id: problem for problem in ProblemStore(DATA_ROOT).all()}
    claims = latest_by_attempt(log.claims())
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

    print(_render(rows, datetime.now(UTC)))
    if missed:
        noun = "attempt" if missed == 1 else "attempts"
        print(f"\n{missed} {noun} grouped nowhere — no technique resolved")


def _render(rows: list[TechniqueRow], now: datetime) -> str:
    """Fixed-width columns, in the order the caller settled on."""
    header = ("technique", "attempts", "solved", "last", "labels")
    body = [
        (
            row.technique,
            str(row.attempt_count),
            f"{row.solved_count}/{row.attempt_count}",
            f"{row.last_attempt_at:%Y-%m-%d} ({(now - row.last_attempt_at).days}d)",
            " ".join(f"{mode}:{count}" for mode, count in sorted(row.self_labels.items())),
        )
        for row in rows
    ]
    widths = [max(len(cell) for cell in column) for column in zip(header, *body, strict=True)]
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *body)
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="algo-coach")
    sub = parser.add_subparsers(dest="command", required=True)

    push_parser = sub.add_parser("push", help="ingest pushed records from JSONL")
    push_parser.add_argument("kind", choices=["attempts", "problems"])
    push_parser.add_argument("source", help="path to a JSONL file, or - for stdin")
    _user_argument(push_parser)

    board_parser = sub.add_parser("board", help="per-technique standing, derived from the log")
    board_parser.add_argument("--json", action="store_true", help="emit rows instead of a table")
    board_parser.add_argument(
        "--stale", action="store_true", help="order by recency, least recently practised first"
    )
    _user_argument(board_parser)

    args = parser.parse_args()
    if args.command == "board":
        _board(args)
    else:
        _push(args, parser)


if __name__ == "__main__":
    main()
