import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path

from algo_coach.ingest import ingest_attempts, ingest_problems
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore


class BadLine(Exception):
    """Not JSON at all: corrupt transport, not an invalid record. Ingest never
    sees it, so it cannot come back as a rejection."""


def read_jsonl(source: str) -> Iterator[dict]:
    """One record per line, so a half-written file is still half-ingestible."""
    lines = sys.stdin if source == "-" else Path(source).read_text().splitlines()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            raise BadLine(f"line {number}: {exc.msg}") from exc


def push(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    records = read_jsonl(args.source)
    try:
        if args.kind == "attempts":
            result = ingest_attempts(
                records,
                user_id=args.user,
                log=AttemptLog(root),
                problems=ProblemStore(root),
            )
        else:
            result = ingest_problems(records, user_id=args.user, store=ProblemStore(root))
    except BadLine as exc:
        # Records before it are stored; re-pushing the fixed file is a no-op
        # on those, so resuming means running the command again.
        parser.exit(2, f"push: {exc}\n")

    print(result.model_dump_json(indent=2))
    if result.rejected:
        parser.exit(1)
