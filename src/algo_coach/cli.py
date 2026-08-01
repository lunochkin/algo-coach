import argparse
import json
import os
import sys
from collections.abc import Iterator
from pathlib import Path

from algo_coach.cards import Card, CardStore
from algo_coach.eval import agreement
from algo_coach.ingest import ingest_attempts
from algo_coach.log import AttemptLog

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

    sub.add_parser("eval", help="agreement report: diagnoses vs self-labels")
    sub.add_parser("classify", help="diagnose unclassified attempts (Phase 1 slice)")

    cards_parser = sub.add_parser("cards", help="cards operations")
    cards_sub = cards_parser.add_subparsers(dest="cards_command", required=True)
    cards_sub.add_parser("seed", help="seed cards")

    push_parser = sub.add_parser("push", help="ingest pushed attempts from JSONL")
    push_parser.add_argument("source", help="path to a JSONL file, or - for stdin")
    push_parser.add_argument(
        "--user",
        default=os.environ.get("ALGO_COACH_USER", "local"),
        help="identity to stamp on ingested records; stands in for authentication",
    )

    args = parser.parse_args()
    log = AttemptLog(DATA_ROOT)

    if args.command == "cards":
        cstore = CardStore(DATA_ROOT)
        if args.cards_command == "seed":
            cards = [
                Card(name="monotonic-stack"),
                Card(name="backtracking"),
            ]
            for card in cards:
                try:
                    cstore.create_card(card)
                    print(f"created: {card.name}")
                except FileExistsError:
                    print(f"skipped: {card.name}")
    elif args.command == "push":
        result = ingest_attempts(_read_jsonl(args.source), user_id=args.user, log=log)
        print(result.model_dump_json(indent=2))
        if result.rejected:
            parser.exit(1)
    elif args.command == "eval":
        report = agreement(log.attempts(), log.diagnoses())
        print(report.model_dump_json(indent=2))
    elif args.command == "classify":
        parser.exit(2, "classify: not implemented yet (next slice)\n")


if __name__ == "__main__":
    main()
