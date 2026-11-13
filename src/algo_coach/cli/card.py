"""`card check`: an authored card checked before it is seeded."""

import argparse
import json
from pathlib import Path

from algo_coach.cards.check import Finding, check_card, siblings

# where a bare slug is looked for: the content repository's cards
CARDS = Path("content/cards")


def card(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    paths = [_path(one) for one in args.cards]
    missing = [str(one) for one in paths if not one.is_file()]
    if missing:
        parser.exit(2, f"card: no such card file: {', '.join(missing)}\n")
    found: list[Finding] = []
    for path in paths:
        mine = check_card(path, siblings(path.parent), mutate=not args.no_mutants)
        found += mine
        if not args.json:
            print(f"{path}: {'ok' if not mine else f'{len(mine)} finding(s)'}")
            for one in mine:
                where = f"{one.template}: " if one.template else ""
                print(f"  [{one.check}] {where}{one.message}")
    if args.json:
        print(json.dumps([one.model_dump() for one in found], indent=2))
    # a survivor may be equivalent to the form, and a stale acceptance names a
    # line that moved, so neither blocks
    if any(one.check not in ("mutant", "stale") for one in found):
        parser.exit(1)


def _path(name: str) -> Path:
    path = Path(name)
    return path if path.suffix == ".json" else CARDS / f"{name}.json"
