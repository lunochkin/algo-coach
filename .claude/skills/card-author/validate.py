"""Check an authored card before it is seeded.

Four things the author cannot see by reading the file: whether it matches
`CardSeed`, whether the technique code is one the vocabulary carries, whether
each template parses, and whether a template's form passes the cases authored
beside it. The trainer runs a recalled form against those cases, so a case the
form itself fails would fail every reproduction of it.

Usage: uv run python .claude/skills/card-author/validate.py
content/cards/*.json
"""

import sys
from pathlib import Path

from pydantic import ValidationError

from algo_coach.runner import agrees, defines_solve, run
from algo_coach.schema import CardSeed, TemplateKind, TemplateSeed
from algo_coach.sitting import DRILL_CAP_MS
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
        if template.kind is not TemplateKind.CODE:
            continue  # a procedure is steps to reproduce, not source
        try:
            compile(template.code, f"{card.slug}/{template.slug}", "exec")
        except SyntaxError as error:
            found.append(f"template {template.slug} does not parse: {error}")
            continue
        found.extend(f"template {template.slug}: {one}" for one in recallable(template))
    return found


def recallable(template: TemplateSeed) -> list[str]:
    """What stops the trainer checking a reproduction of this form."""
    if not template.cases:
        return []  # read on the card, and never offered for recall
    if not defines_solve(template.code):
        return ["the cases call `solve`, and the form defines no module-level `solve`"]
    found = []
    for index, case in enumerate(template.cases):
        (ran,) = run(template.code, [case.args], cap_ms=DRILL_CAP_MS)
        if not ran.returned:
            raised = "" if ran.error is None else f": {ran.error.splitlines()[-1]}"
            found.append(f"case {index} {ran.outcome}{raised}")
        elif not agrees(ran.value, case.expected):
            found.append(f"case {index} returned {ran.value!r}, not {case.expected!r}")
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
