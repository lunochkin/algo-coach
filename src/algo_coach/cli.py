import argparse
import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path

from algo_coach.ingest import ingest_attempts, ingest_problems
from algo_coach.log import AttemptLog
from algo_coach.problems import ProblemStore

DATA_ROOT = Path("data")


def _read_jsonl(source: str) -> Iterator[dict]:
    """One record per line, so a half-written file is still half-ingestible."""
    lines = sys.stdin if source == "-" else Path(source).read_text().splitlines()
    for line in lines:
        if line.strip():
            yield json.loads(line)


def main() -> None:
    parser = argparse.ArgumentParser(prog="algo-coach")
    sub = parser.add_subparsers(dest="command", required=True)

    push_parser = sub.add_parser("push", help="ingest pushed records from JSONL")
    push_parser.add_argument("kind", choices=["attempts", "problems"])
    push_parser.add_argument("source", help="path to a JSONL file, or - for stdin")
    push_parser.add_argument(
        "--user",
        default=os.environ.get("ALGO_COACH_USER", "local"),
        help="identity to stamp on ingested records; stands in for authentication",
    )

    args = parser.parse_args()
    log = AttemptLog(DATA_ROOT)

    if args.command == "push":
        records = _read_jsonl(args.source)
        if args.kind == "attempts":
            result = ingest_attempts(records, user_id=args.user, log=log)
        else:
            result = ingest_problems(
                records, user_id=args.user, store=ProblemStore(DATA_ROOT)
            )
        print(result.model_dump_json(indent=2))
        if result.rejected:
            parser.exit(1)


if __name__ == "__main__":
    main()
