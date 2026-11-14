import argparse
from pathlib import Path

from climb.knowledge.learn import imported
from climb.storage import Database


def knowledge(args: argparse.Namespace, parser: argparse.ArgumentParser, root: Database) -> None:
    try:
        report = imported(root, args.user, Path(args.source))
    except (OSError, ValueError) as exc:
        parser.exit(2, f"knowledge import: {exc}\n")
    print(report.model_dump_json(indent=2))
