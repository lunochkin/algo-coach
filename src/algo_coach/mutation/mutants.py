"""Mutants of a canonical: the same solution with one change to its syntax
tree.

Nothing is stored. The set re-derives from the canonical whenever the operators
below change, and a mutant no case kills names a case that has to exist.
"""

import ast
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from functools import partial
from typing import Any, cast


class Operator(StrEnum):
    """What made a mutant. Reported per mutant, so a survivor names the kind of
    mistake its missing case has to catch."""

    BOUNDARY = "boundary"
    NEGATION = "negation"
    ARITHMETIC = "arithmetic"
    CONNECTOR = "connector"
    CONDITION = "condition"
    CONSTANT = "constant"
    EXTREMUM = "extremum"
    CONTROL = "control"


BOUNDARY = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt}
NEGATED = {
    ast.Lt: ast.GtE,
    ast.LtE: ast.Gt,
    ast.Gt: ast.LtE,
    ast.GtE: ast.Lt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
}
ARITHMETIC = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult}
CONNECTOR = {ast.And: ast.Or, ast.Or: ast.And}
EXTREMUM = {"min": "max", "max": "min"}

SYMBOL = {
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Is: "is",
    ast.IsNot: "is not",
    ast.In: "in",
    ast.NotIn: "not in",
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.FloorDiv: "//",
    ast.And: "and",
    ast.Or: "or",
}


@dataclass(frozen=True)
class Mutant:
    """The canonical with one change, and what that change was."""

    code: str
    operator: Operator
    change: str
    line: int


def mutants(code: str) -> list[Mutant]:
    """Every one-change mutant, in tree order."""
    sites = _Walk().collect(ast.parse(code))
    return [_mutate(code, index, site) for index, site in enumerate(sites)]


@dataclass(frozen=True)
class _Site:
    operator: Operator
    change: str
    line: int


def _mutate(code: str, target: int, site: _Site) -> Mutant:
    # a parse per mutant: the walk rewrites in place, so one tree cannot carry
    # two changes
    tree = _Walk(target=target).visit(ast.parse(code))
    return Mutant(
        code=ast.unparse(tree), operator=site.operator, change=site.change, line=site.line
    )


class _Walk(ast.NodeTransformer):
    """One walk, used to enumerate the sites and to rewrite the nth."""

    def __init__(self, target: int | None = None) -> None:
        self.target = target
        self.sites: list[_Site] = []

    def collect(self, tree: ast.AST) -> list[_Site]:
        self.visit(tree)
        return self.sites

    def _offer(
        self,
        node: ast.AST,
        operator: Operator,
        change: str,
        rewrite: Callable[[], ast.AST],
    ) -> ast.AST | None:
        hit = len(self.sites) == self.target
        self.sites.append(_Site(operator, change, getattr(node, "lineno", 0)))
        return rewrite() if hit else None

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        self.generic_visit(node)
        out: ast.AST = node
        for index, op in enumerate(node.ops):
            for operator, table in ((Operator.BOUNDARY, BOUNDARY), (Operator.NEGATION, NEGATED)):
                new = table.get(type(op))
                if new is None:
                    continue
                out = (
                    self._offer(
                        node, operator, _label(op, new), partial(_swap_at, node, index, new)
                    )
                    or out
                )
        return out

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        return self._arithmetic(node) or node

    def visit_AugAssign(self, node: ast.AugAssign) -> ast.AST:
        self.generic_visit(node)
        return self._arithmetic(node) or node

    def _arithmetic(self, node: ast.BinOp | ast.AugAssign) -> ast.AST | None:
        new = ARITHMETIC.get(type(node.op))
        if new is None:
            return None
        return self._offer(
            node, Operator.ARITHMETIC, _label(node.op, new), partial(_swap, node, new)
        )

    def visit_BoolOp(self, node: ast.BoolOp) -> ast.AST:
        self.generic_visit(node)
        new = CONNECTOR[type(node.op)]
        return (
            self._offer(node, Operator.CONNECTOR, _label(node.op, new), partial(_swap, node, new))
            or node
        )

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        self.generic_visit(node)
        if not isinstance(node.op, ast.Not):
            return node
        return self._offer(node, Operator.CONDITION, "not dropped", partial(_drop, node)) or node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        # `is int` rather than `isinstance`: a shifted `True` is 2, which is
        # neither a boundary nor a value the solution could have been written
        # with
        if type(node.value) is not int:
            return node
        out: ast.AST = node
        for delta in (1, -1):
            change = f"{node.value} → {node.value + delta}"
            out = self._offer(node, Operator.CONSTANT, change, partial(_shift, node, delta)) or out
        return out

    def visit_Name(self, node: ast.Name) -> ast.AST:
        other = EXTREMUM.get(node.id)
        if other is None:
            return node
        change = f"{node.id} → {other}"
        return self._offer(node, Operator.EXTREMUM, change, partial(_rename, node, other)) or node

    def visit_Break(self, node: ast.Break) -> ast.AST:
        return self._offer(node, Operator.CONTROL, "break → continue", partial(_jump, node)) or node

    def visit_Continue(self, node: ast.Continue) -> ast.AST:
        return self._offer(node, Operator.CONTROL, "continue → break", partial(_jump, node)) or node


def _label(op: ast.AST, new: type[ast.AST]) -> str:
    return f"{SYMBOL[type(op)]} → {SYMBOL[new]}"


def _swap_at(node: ast.Compare, index: int, new: type[ast.cmpop]) -> ast.AST:
    node.ops[index] = new()
    return node


def _swap(node: ast.BinOp | ast.AugAssign | ast.BoolOp, new: type[ast.AST]) -> ast.AST:
    # an operator on two of the three and a boolop on the third
    node.op = cast(Any, new())
    return node


def _drop(node: ast.UnaryOp) -> ast.AST:
    return node.operand


def _shift(node: ast.Constant, delta: int) -> ast.AST:
    assert isinstance(node.value, int)  # matched on an integer literal
    return ast.copy_location(ast.Constant(value=node.value + delta), node)


def _rename(node: ast.Name, name: str) -> ast.AST:
    node.id = name
    return node


def _jump(node: ast.Break | ast.Continue) -> ast.AST:
    jump = ast.Continue() if isinstance(node, ast.Break) else ast.Break()
    return ast.copy_location(jump, node)


__all__ = [
    "ARITHMETIC",
    "BOUNDARY",
    "CONNECTOR",
    "EXTREMUM",
    "NEGATED",
    "Mutant",
    "Operator",
    "mutants",
]
