"""Check an authored card before it is seeded.

Three things the author cannot see by reading the file: whether it matches
`CardSeed`, whether the technique code is one the vocabulary carries, and
whether each template parses. Compiling is not passing — the trainer runs the
templates for real — but it catches a truncated paste at authoring time.

Usage: uv run python .claude/skills/card-author/validate.py content/cards/*.json
"""

import sys
from pathlib import Path

from pydantic import ValidationError

from algo_coach.schema import CardSeed
from algo_coach.techniques import is_known


def problems(path: Path) -> list[str]:
    try:
        card = CardSeed.model_validate_json(path.read_text())
    except ValidationError as error:
        return [str(error)]

    found = []
    if not is_known(card.technique):
        found.append(f"unknown technique code: {card.technique}")
    if not is_known(card.selector.technique):
        found.append(f"unknown selector technique: {card.selector.technique}")
    if path.stem != card.slug:
        found.append(f"file name {path.stem} does not match slug {card.slug}")
    for template in card.templates:
        try:
            compile(template.code, f"{card.slug}/{template.slug}", "exec")
        except SyntaxError as error:
            found.append(f"template {template.slug} does not parse: {error}")
    return found


def main(paths: list[str]) -> int:
    failed = False
    for name in paths:
        path = Path(name)
        found = problems(path)
        failed |= bool(found)
        print(f"{path}: {'ok' if not found else ''}")
        for problem in found:
            print(f"  {problem}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
