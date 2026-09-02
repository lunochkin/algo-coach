import argparse
import json
from collections.abc import Iterator
from pathlib import Path

from algo_coach.cards import CardStore, seed_cards


class BadLine(Exception):
    """Not JSON at all: a corrupt file, not an invalid record."""


def read_json(source: str) -> Iterator[dict]:
    """One authored file per record: a directory of them, or a single file."""
    path = Path(source)
    paths = sorted(path.glob("*.json")) if path.is_dir() else [path]
    for file in paths:
        try:
            yield json.loads(file.read_text())
        except json.JSONDecodeError as exc:
            raise BadLine(f"{file}: {exc.msg}") from exc


def seed(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Path) -> None:
    try:
        result = seed_cards(read_json(args.source), store=CardStore(root))
    except (BadLine, OSError) as exc:
        parser.exit(2, f"seed: {exc}\n")

    print(result.model_dump_json(indent=2))
    if result.rejected:
        parser.exit(1)
