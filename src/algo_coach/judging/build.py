"""Judgement items built from the seeded templates: `content.md`, Judgement
items."""

import ast
import hashlib
import io
import tokenize
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from algo_coach.cards.check import CAP_MS, passes
from algo_coach.ids import new_id
from algo_coach.mutation import Mutant, mutants, pace
from algo_coach.runner import run
from algo_coach.schema import (
    Card,
    CaseOutcome,
    ItemStatus,
    JudgementItem,
    Template,
    TemplateKind,
)

# the widest line an item shows: the modules' width, wrapped once on a phone
WIDTH = 60
# flawed items per template, beside one clean: a quarter of the items clean
FLAWED = 3


def digest(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def shown(code: str, harness: Sequence[str]) -> str:
    """The code as an item shows it: no comments, no harness, no blank runs."""
    tree = ast.parse(code)
    hidden = _harness_lines(tree, harness)
    comments: dict[int, int] = {}
    for token in tokenize.generate_tokens(io.StringIO(code).readline):
        if token.type == tokenize.COMMENT:
            comments[token.start[0]] = token.start[1]
    kept: list[str] = []
    for number, line in enumerate(code.splitlines(), 1):
        if number in hidden:
            continue
        text = line[: comments[number]].rstrip() if number in comments else line.rstrip()
        if text or line.strip() == "":
            kept.append(text)
    lines = [one for index, one in enumerate(kept) if one or (index and kept[index - 1])]
    return "\n".join(lines).strip("\n") + "\n"


def items(template: Template, *, now: datetime) -> list[JudgementItem]:
    """One clean item and up to three flawed, or none where no flaw fits."""
    if template.kind is not TemplateKind.CODE or not template.cases:
        return []
    form = shown(template.code, template.harness)
    if _width(form) > WIDTH:
        return []
    args = [case.args for case in template.cases]
    ran = run(template.code, args, cap_ms=CAP_MS)
    cap = pace(max((one.elapsed_ms or 0 for one in ran), default=0), cap_ms=CAP_MS)
    hidden = _harness_lines(ast.parse(template.code), template.harness)
    flaws = [
        flaw
        for one in mutants(template.code)
        if one.line not in hidden and (flaw := _flaw(template, form, one, args, cap))
    ]
    if not flaws:
        return []
    base: dict[str, Any] = {
        "created_at": now,
        "template_id": template.id,
        "form_digest": digest(template.code),
    }
    clean = JudgementItem.model_validate(base | {"id": new_id(), "code": form, "clean": True})
    return [clean] + [
        JudgementItem.model_validate(base | one | {"id": new_id(), "clean": False})
        for one in _spread(flaws)
    ]


def build(
    cards: Sequence[Card], held: Sequence[JudgementItem], *, now: datetime
) -> tuple[list[JudgementItem], list[str]]:
    """The items to add and the ids to retire: a template already served at its
    current code is left alone."""
    served: dict[str, list[JudgementItem]] = {}
    for one in held:
        if one.status is ItemStatus.SERVED:
            served.setdefault(one.template_id, []).append(one)
    added: list[JudgementItem] = []
    retired: list[str] = []
    for card in cards:
        for template in card.templates:
            current = served.get(template.id, [])
            if current and all(one.form_digest == digest(template.code) for one in current):
                continue
            retired += [one.id for one in current]
            added += items(template, now=now)
    return added, retired


def _flaw(
    template: Template, form: str, mutant: Mutant, args: list[list[Any]], cap: int
) -> dict[str, Any] | None:
    if mutant.span is None or mutant.text is None:
        return None  # a change spanning lines cannot be shown on one
    view = shown(_spliced(template.code, mutant.span, mutant.text), template.harness)
    before, after = form.splitlines(), view.splitlines()
    if len(before) != len(after) or _width(view) > WIDTH:
        return None
    moved = [number for number, (a, b) in enumerate(zip(before, after, strict=True), 1) if a != b]
    if len(moved) != 1:
        return None
    ran = run(mutant.code, args, cap_ms=cap, stop_early=True)
    for case, one in zip(template.cases, ran, strict=False):
        if passes(one, case.expected, template):
            continue
        outcome = CaseOutcome(str(one.outcome)) if not one.returned else CaseOutcome.WRONG
        if outcome is CaseOutcome.TIMEOUT:
            return None  # a slowdown is not read off the code
        return {
            "code": view,
            "line": moved[0],
            "change": mutant.change,
            "case_args": case.args,
            "case_expected": case.expected,
            "outcome": outcome,
            "returned": one.value if one.returned else None,
        }
    return None


def _spliced(code: str, span: tuple[int, int, int], text: str) -> str:
    """The author's code with one node replaced, its formatting kept."""
    number, start, end = span
    lines = code.splitlines(keepends=True)
    # the parser's columns count UTF-8 bytes, not characters
    line = lines[number - 1].encode()
    lines[number - 1] = (line[:start] + text.encode() + line[end:]).decode()
    return "".join(lines)


def _spread(flaws: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Up to `FLAWED` flaws on different lines, spread over the form."""
    first: dict[int, dict[str, Any]] = {}
    for one in flaws:
        first.setdefault(one["line"], one)
    lines = sorted(first)
    if len(lines) <= FLAWED:
        return [first[line] for line in lines]
    picked = {round(index * (len(lines) - 1) / (FLAWED - 1)) for index in range(FLAWED)}
    return [first[lines[index]] for index in sorted(picked)]


def _harness_lines(tree: ast.Module, harness: Sequence[str]) -> set[int]:
    lines: set[int] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.ClassDef) and node.name in harness:
            start = min([node.lineno, *(one.lineno for one in node.decorator_list)])
            lines.update(range(start, (node.end_lineno or node.lineno) + 1))
    return lines


def _width(code: str) -> int:
    return max((len(line) for line in code.splitlines()), default=0)
