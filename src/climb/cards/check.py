"""An authored card checked before it is seeded: what the author cannot see by
reading the file. `content.md` gives what a template's cases are for."""

import ast
import json
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ValidationError

from climb.cards.graph import broken
from climb.mutation import Mutant, mutants, pace
from climb.runner import CaseRun, agrees, as_json, defines_solve, run
from climb.schema import CardSeed, Json, Template, TemplateKind, TemplateSeed
from climb.techniques import is_known

# the sitting's cap: a recall is judged under it
CAP_MS = 2000

# a repeated mutant name is numbered from its second occurrence
ORDINALS = {2: "nd", 3: "rd"}


class Finding(BaseModel):
    card: str  # the file's stem, so a card that does not parse is still named
    template: str | None = None
    check: str  # schema, technique, slug, graph, parse, harness, solve, case, mutant or stale
    message: str


def siblings(folder: Path) -> dict[str, CardSeed]:
    """The cards a requirement may name: the seed checks the same graph."""
    found: dict[str, CardSeed] = {}
    for path in sorted(folder.glob("*.json")):
        try:
            one = CardSeed.model_validate_json(path.read_text())
        except ValidationError:
            continue  # reported when that file is checked
        found[one.slug] = one
    return found


def check_card(path: Path, others: Mapping[str, CardSeed], *, mutate: bool = True) -> list[Finding]:
    """Every finding on one card file, the template ones in template order."""
    name = path.stem
    try:
        card = CardSeed.model_validate_json(path.read_text())
    except (ValidationError, json.JSONDecodeError) as error:
        return [Finding(card=name, check="schema", message=str(error))]
    found = [
        Finding(card=name, check="technique", message=f"unknown technique code: {code}")
        for code in dict.fromkeys((card.technique, card.selector.technique))
        if not is_known(code)
    ]
    if name != card.slug:
        found.append(Finding(card=name, check="slug", message=f"the slug is {card.slug}"))
    refused = broken({**others, card.slug: card})
    if card.slug in refused:
        found.append(Finding(card=name, check="graph", message=refused[card.slug]))
    for template in card.templates:
        found += [
            Finding(card=name, template=template.slug, check=check, message=message)
            for check, message in _template(template, mutate=mutate)
        ]
    return found


def _template(template: TemplateSeed, *, mutate: bool) -> list[tuple[str, str]]:
    if template.kind is not TemplateKind.CODE:
        return []  # a procedure is steps to reproduce, not source
    try:
        tree = ast.parse(template.code, template.slug)
    except SyntaxError as error:
        return [("parse", f"does not parse: {error}")]
    defined = {node.name for node in tree.body if isinstance(node, ast.FunctionDef | ast.ClassDef)}
    missing = [name for name in template.harness if name not in defined]
    if missing:
        return [("harness", f"names no top-level definition: {', '.join(missing)}")]
    if not template.cases:
        return []  # read on the card, and never offered for recall
    if not defines_solve(template.code):
        return [("solve", "the cases call `solve`, and the form defines no module-level `solve`")]
    ran = run(template.code, [case.args for case in template.cases], cap_ms=CAP_MS)
    failed = [
        ("case", f"case {index} {_reading(one)}")
        for index, (case, one) in enumerate(zip(template.cases, ran, strict=True))
        if not passes(one, case.expected, template)
    ]
    if failed or not mutate:
        return failed
    slowest = max((one.elapsed_ms or 0 for one in ran), default=0)
    survivors = _survivors(template, cap_ms=pace(slowest, cap_ms=CAP_MS))
    standing = [names[one] for one in survivors] if (names := _names(template.code)) else []
    accepted = set(template.equivalent)
    return [("mutant", f"{one} survives every case") for one in standing if one not in accepted] + [
        ("stale", f"{one} is accepted as equivalent, and no mutant survives as it")
        for one in template.equivalent
        if one not in standing
    ]


def _survivors(template: TemplateSeed, *, cap_ms: int) -> list[Mutant]:
    args = [case.args for case in template.cases]
    standing: list[Mutant] = []
    for mutant in mutants(template.code):
        ran = run(mutant.code, args, cap_ms=cap_ms, stop_early=True)
        if len(ran) == len(args) and all(
            passes(one, case.expected, template)
            for case, one in zip(template.cases, ran, strict=True)
        ):
            standing.append(mutant)
    return standing


def _names(code: str) -> dict[Mutant, str]:
    """Each mutant's name in a report and in `equivalent`. Two mutants can make
    the same change on one line, so a repeat is numbered in tree order."""
    seen: dict[str, int] = {}
    named: dict[Mutant, str] = {}
    for one in mutants(code):
        base = f"line {one.line}: {one.change}"
        seen[base] = seen.get(base, 0) + 1
        named[one] = base if seen[base] == 1 else f"{base} ({_ordinal(seen[base])})"
    return named


def _ordinal(n: int) -> str:
    return f"{n}{ORDINALS.get(n, 'th')}"


def passes(ran: CaseRun, expected: Json, template: TemplateSeed | Template) -> bool:
    """A case passed, a set answer compared in any order."""
    return ran.returned and agrees(_settled(ran.value, template), _settled(expected, template))


def _settled(value: Json, template: TemplateSeed | Template) -> Json:
    # a set answer's top level sorted: two correct reproductions emit it in
    # different orders
    if not template.unordered or not isinstance(value, list):
        return value
    return sorted(value, key=as_json)


def _reading(ran: CaseRun) -> str:
    if ran.returned:
        return f"returned {ran.value!r}, not the expected value"
    return f"{ran.outcome}" + (f": {ran.error.splitlines()[-1]}" if ran.error else "")


__all__ = ["CAP_MS", "Finding", "check_card", "passes", "siblings"]
