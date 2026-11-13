"""An authored card checked before it is seeded: what the author cannot see by
reading the file. `content.md` gives what a template's cases are for."""

import json
from collections.abc import Mapping
from pathlib import Path

from pydantic import BaseModel, ValidationError

from algo_coach.cards.graph import broken
from algo_coach.mutation import Mutant, mutants, pace
from algo_coach.runner import CaseRun, agrees, as_json, defines_solve, run
from algo_coach.schema import CardSeed, Json, TemplateKind, TemplateSeed
from algo_coach.techniques import is_known

# the sitting's cap: a recall is judged under it
CAP_MS = 2000


class Finding(BaseModel):
    card: str  # the file's stem, so a card that does not parse is still named
    template: str | None = None
    check: str  # schema, technique, slug, graph, parse, solve, case or mutant
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
        compile(template.code, template.slug, "exec")
    except SyntaxError as error:
        return [("parse", f"does not parse: {error}")]
    if not template.cases:
        return []  # read on the card, and never offered for recall
    if not defines_solve(template.code):
        return [("solve", "the cases call `solve`, and the form defines no module-level `solve`")]
    ran = run(template.code, [case.args for case in template.cases], cap_ms=CAP_MS)
    failed = [
        ("case", f"case {index} {_reading(one)}")
        for index, (case, one) in enumerate(zip(template.cases, ran, strict=True))
        if not _passes(one, case.expected, template)
    ]
    if failed or not mutate:
        return failed
    slowest = max((one.elapsed_ms or 0 for one in ran), default=0)
    return [
        ("mutant", f"line {one.line}: {one.change} survives every case")
        for one in _survivors(template, cap_ms=pace(slowest, cap_ms=CAP_MS))
    ]


def _survivors(template: TemplateSeed, *, cap_ms: int) -> list[Mutant]:
    args = [case.args for case in template.cases]
    standing: list[Mutant] = []
    for mutant in mutants(template.code):
        ran = run(mutant.code, args, cap_ms=cap_ms, stop_early=True)
        if len(ran) == len(args) and all(
            _passes(one, case.expected, template)
            for case, one in zip(template.cases, ran, strict=True)
        ):
            standing.append(mutant)
    return standing


def _passes(ran: CaseRun, expected: Json, template: TemplateSeed) -> bool:
    return ran.returned and agrees(_settled(ran.value, template), _settled(expected, template))


def _settled(value: Json, template: TemplateSeed) -> Json:
    # a set answer's top level sorted: two correct reproductions emit it in
    # different orders
    if not template.unordered or not isinstance(value, list):
        return value
    return sorted(value, key=as_json)


def _reading(ran: CaseRun) -> str:
    if ran.returned:
        return f"returned {ran.value!r}, not the expected value"
    return f"{ran.outcome}" + (f": {ran.error.splitlines()[-1]}" if ran.error else "")


__all__ = ["CAP_MS", "Finding", "check_card", "siblings"]
